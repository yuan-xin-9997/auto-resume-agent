"""OpenCode's documented HTTP API; never reads provider credentials or approves tools."""
import base64
import email.utils
import http.client
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from .protocol import BackendError
from .model import numeric

V2_GO_WINDOWS = (("rolling", "rolling", 300), ("weekly", "weekly", 10080), ("monthly", "monthly", 43200))


def valid_session(value):
    return isinstance(value, str) and re.fullmatch(r"ses_[A-Za-z0-9]{1,128}", value) is not None


def valid_message(value):
    return isinstance(value, str) and re.fullmatch(r"msg_[A-Za-z0-9]{1,128}", value) is not None


def endpoint(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise BackendError("opencode_invalid_url")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise BackendError("opencode_remote_requires_https")
    try:
        parsed.port
    except ValueError:
        raise BackendError("opencode_invalid_url") from None
    return value.rstrip("/")


def normalize(info):
    if not isinstance(info, dict) or not valid_message(info.get("id")):
        raise BackendError("opencode_unknown_message")
    timing = info.get("time")
    if timing is None:
        timing = {}
    if not isinstance(timing, dict):
        raise BackendError("opencode_response_incompatible")
    completed = timing.get("completed")
    turn = {"id": info["id"], "status": "completed", "completedAt": completed / 1000 if numeric(completed) else None}
    error = info.get("error")
    if info.get("role") != "assistant" or not isinstance(error, dict):
        return turn
    data = error.get("data")
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise BackendError("opencode_response_incompatible")
    if error.get("name") != "APIError" or data.get("isRetryable") is not True:
        return turn
    # A billing denial can use HTTP 429; it is not a temporary rate limit.
    # Accept both the documented JSON string and an already-decoded object.
    body = data.get("responseBody")
    denial = {}
    if isinstance(body, dict):
        denial = body.get("error") if isinstance(body.get("error"), dict) else body
    elif isinstance(body, str) and body.strip():
        try:
            parsed = json.loads(body)
        except (ValueError, TypeError):
            # Unstructured denial text must not turn a 429 into a blind retry.
            return turn
        if not isinstance(parsed, dict):
            return turn
        denial = parsed.get("error") if isinstance(parsed.get("error"), dict) else parsed
    elif body is not None:
        return turn
    if isinstance(denial, dict) and (denial.get("code") in (
            "insufficient_quota", "billing_hard_limit_reached", "credits_exhausted")
            or denial.get("type") == "insufficient_quota"):
        return turn
    status = data.get("statusCode")
    if status == 429:
        code = "rateLimitExceeded"
    elif status in (408, 425) or status is None:
        code = "httpConnectionFailed"
    elif type(status) is int and 500 <= status <= 599:
        code = "internalServerError"
    else:
        return turn
    turn.update(status="failed", error={"codexErrorInfo": code})
    headers = data.get("responseHeaders") or {}
    if not isinstance(headers, dict):
        headers = {}
    value = next((v for k, v in headers.items()
                  if isinstance(k, str) and k.lower() == "retry-after"), None)
    if value is not None and turn["completedAt"] is not None:
        try:
            seconds = float(value)
            if numeric(seconds) and seconds >= 0:
                turn["retryAt"] = turn["completedAt"] + seconds
        except (ValueError, TypeError):
            try:
                date = email.utils.parsedate_to_datetime(value)
                if date.tzinfo:
                    turn["retryAt"] = date.timestamp()
            except (ValueError, TypeError, OverflowError):
                pass
    return turn


def _structured_body(error):
    """Return the decoded provider error inside response.body without trusting text."""
    body = error.get("response")
    if isinstance(body, dict):
        body = body.get("body")
    if isinstance(body, dict):
        inner = body.get("error")
        return inner if isinstance(inner, dict) else body
    if isinstance(body, str) and body.strip():
        try:
            parsed = json.loads(body)
        except (ValueError, TypeError):
            return {}
        if isinstance(parsed, dict):
            inner = parsed.get("error")
            return inner if isinstance(inner, dict) else parsed
    return {}


def _v2_error_code(info, error, go_limited=False):
    denial = _structured_body(error)
    if denial.get("code") in ("insufficient_quota", "billing_hard_limit_reached",
                              "credits_exhausted", "billing_error", "payment_required"):
        return None
    if denial.get("type") in ("insufficient_quota", "billing_error", "BillingError"):
        return None
    kind = error.get("type")
    status = error.get("status")
    if kind == "provider.transport":
        return "httpConnectionFailed"
    if kind == "provider.free-limit":
        return "rateLimitExceeded" if status in (429, None) else None
    if kind == "provider.quota":
        model = info.get("model")
        provider = model.get("providerID") if isinstance(model, dict) else None
        if denial.get("type") == "GoUsageLimitError" or (go_limited and provider == "opencode-go"):
            return "usageLimitExceeded"
        return "rateLimitExceeded" if status in (429, None) else None
    if kind == "provider.error":
        if status in (408, 425):
            return "httpConnectionFailed"
        if status == 429:
            return "rateLimitExceeded"
        if type(status) is int and 500 <= status <= 599:
            return "internalServerError"
    return None


def normalize_v2(info, go_limited=False):
    """Normalize OpenCode 2.x assistant or idle message records."""
    if not isinstance(info, dict) or not valid_message(info.get("id")):
        raise BackendError("opencode_unknown_message")
    timing = info.get("time")
    if timing is None:
        timing = {}
    if not isinstance(timing, dict):
        raise BackendError("opencode_response_incompatible")
    completed = timing.get("completed")
    if not numeric(completed):
        completed = timing.get("streamed")
    if not numeric(completed):
        completed = timing.get("created")
    turn = {"id": info["id"], "status": "completed",
            "completedAt": completed / 1000 if numeric(completed) else None}
    kind = info.get("type")
    if kind == "idle":
        if info.get("outcome") == "interrupted":
            turn["status"] = "interrupted"
            return turn
        if info.get("outcome") != "failed":
            return turn
    elif kind != "assistant":
        return turn
    error = info.get("error")
    if not isinstance(error, dict):
        return turn
    code = _v2_error_code(info, error, go_limited)
    if code is None:
        return turn
    turn.update(status="failed", error={"codexErrorInfo": code})
    retry = error.get("retryAfterMs")
    if numeric(retry) and retry >= 0 and turn["completedAt"] is not None:
        turn["retryAt"] = turn["completedAt"] + retry / 1000
    return turn


def usage_v2(data):
    """Map the OpenCode 2.x Go allowance to the internal usage snapshot."""
    result = {"available": None, "reset_at": None, "windows": [], "reason": "quota_not_exposed"}
    go = data.get("go") if isinstance(data, dict) else None
    if not isinstance(go, dict):
        return result
    blocked = []
    for key, window, minutes in V2_GO_WINDOWS:
        meter = go.get(key)
        if not isinstance(meter, dict):
            raise BackendError("opencode_response_incompatible")
        percent = meter.get("percent")
        limited = meter.get("limited")
        reset = meter.get("resetsAt")
        if (not numeric(percent) or percent < 0 or not isinstance(limited, bool)
                or not numeric(reset) or reset < 0):
            raise BackendError("opencode_response_incompatible")
        reset_at = reset / 1000 if reset > 0 else None
        result["windows"].append({"bucket": "OpenCode Go", "window": window,
                                  "used_percent": percent, "reset_at": reset_at,
                                  "minutes": minutes})
        if limited or percent >= 100:
            blocked.append(reset_at)
    result["reason"] = "opencode_go"
    if blocked:
        result["available"] = False
        if all(item is not None for item in blocked):
            result["reset_at"] = max(blocked)
    elif result["windows"]:
        result["available"] = True
    return result


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class OpenCode:
    agent = "opencode"
    quota_required = False
    valid_turn_id = staticmethod(valid_message)

    def __init__(self, url="http://127.0.0.1:4096", directory="", timeout=15):
        self.url = endpoint(url)
        self.directory = directory
        self.timeout = timeout
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.routes = {}
        self.mode = None
        self._go_limited = False

    def _headers(self, body):
        headers = {"Accept": "application/json"}
        password = os.environ.get("OPENCODE_SERVER_PASSWORD")
        if password:
            credentials = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode") + ":" + password
            headers["Authorization"] = "Basic " + base64.b64encode(credentials.encode()).decode()
        if body is not None:
            headers["Content-Type"] = "application/json"
        return headers

    def _fetch(self, path, body=None, params=None):
        query = dict(params or {})
        # The 1.19.x API scopes every route with a plain directory query. The
        # 2.x API uses location[directory] only on the routes that need it.
        if self.mode != "v2" and self.directory:
            query.setdefault("directory", self.directory)
        url = self.url + path + ("?" + urllib.parse.urlencode(query) if query else "")
        data = json.dumps(body).encode() if body is not None else None
        try:
            with self.opener.open(urllib.request.Request(
                    url, data=data, headers=self._headers(body)), timeout=self.timeout) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
                if len(raw) > 16 * 1024 * 1024:
                    raise BackendError("opencode_response_too_large")
                return response.getcode(), raw
        except urllib.error.HTTPError as error:
            try:
                raw = error.read(16 * 1024 * 1024 + 1)
            except (OSError, http.client.HTTPException):
                raw = b""
            if len(raw) > 16 * 1024 * 1024:
                raw = b""
            return error.code, raw
        except (OSError, urllib.error.URLError, http.client.HTTPException):
            raise BackendError("opencode_connection_failed") from None

    @staticmethod
    def _decode(raw):
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            raise BackendError("opencode_invalid_response") from None

    def request(self, path, body=None, params=None, allow_missing=False):
        status, raw = self._fetch(path, body, params)
        if status >= 400:
            if status == 401:
                raise BackendError("opencode_auth_required")
            if allow_missing and status in (404, 405, 501):
                return None
            raise BackendError("opencode_http_" + str(status))
        return self._decode(raw)

    def _detect(self):
        if self.mode:
            return
        # 1.19.x exposes /global/health. 2.x serves its web UI at that path
        # instead, so a non-JSON 200 or a 404 is expected before probing /api.
        health_status, raw = self._fetch("/global/health")
        health = None
        if health_status == 200:
            try:
                health = self._decode(raw)
            except BackendError:
                health = None
        if isinstance(health, dict) and isinstance(health.get("healthy"), bool):
            self.mode = "v1"
            return
        session_status, raw = self._fetch("/api/session", params={"limit": 1, "parentID": "null"})
        session = None
        if session_status == 200:
            try:
                session = self._decode(raw)
            except BackendError:
                session = None
        if isinstance(session, dict) and isinstance(session.get("data"), list):
            self.mode = "v2"
            return
        if health_status == 401 or session_status == 401:
            raise BackendError("opencode_auth_required")
        if health_status >= 500:
            raise BackendError("opencode_http_" + str(health_status))
        if session_status >= 500:
            raise BackendError("opencode_http_" + str(session_status))
        raise BackendError("opencode_response_incompatible")

    def start(self):
        self._detect()
        if self.mode == "v1":
            value = self.request("/global/health")
            if not isinstance(value, dict):
                raise BackendError("opencode_response_incompatible")
            healthy = value.get("healthy")
            if healthy is False:
                raise BackendError("opencode_unhealthy")
            if healthy is not True:
                raise BackendError("opencode_response_incompatible")

    def usage(self):
        self.start()
        if self.mode != "v2":
            return {"available": None, "reset_at": None, "windows": [], "reason": "quota_not_exposed"}
        params = {"location[directory]": self.directory} if self.directory else None
        value = self.request("/api/experimental/usage/limits", params=params, allow_missing=True)
        data = value.get("data") if isinstance(value, dict) else None
        result = usage_v2(data)
        self._go_limited = result.get("available") is False
        return result

    def threads(self, cursor=None):
        self._detect()
        if self.mode == "v1":
            if cursor:
                raise BackendError("opencode_unexpected_cursor")
            rows = self.request("/session")
            if not isinstance(rows, list):
                raise BackendError("opencode_response_incompatible")
            data = []
            for row in rows:
                if not isinstance(row, dict):
                    raise BackendError("opencode_response_incompatible")
                metadata = self.metadata(row)
                if not row.get("parentID") and not metadata["archived"]:
                    data.append(metadata)
            return {"data": data, "nextCursor": None}
        params = {"limit": 50, "parentID": "null"}
        if self.directory:
            params["directory"] = self.directory
        if cursor:
            params["cursor"] = cursor
        value = self.request("/api/session", params=params)
        if not isinstance(value, dict) or not isinstance(value.get("data"), list):
            raise BackendError("opencode_response_incompatible")
        data = []
        for row in value["data"]:
            metadata = self.metadata_v2(row)
            if not metadata["archived"]:
                data.append(metadata)
        cursor_value = value.get("cursor")
        next_cursor = cursor_value.get("next") if isinstance(cursor_value, dict) else None
        return {"data": data, "nextCursor": next_cursor if isinstance(next_cursor, str) else None}

    @staticmethod
    def metadata(row):
        if not isinstance(row, dict) or not valid_session(row.get("id")):
            raise BackendError("opencode_response_incompatible")
        timing = row.get("time")
        if timing is not None and not isinstance(timing, dict):
            raise BackendError("opencode_response_incompatible")
        parent = row.get("parentID")
        if parent is not None and not isinstance(parent, str):
            raise BackendError("opencode_response_incompatible")
        updated = (timing or {}).get("updated")
        return {"id": row["id"], "name": row.get("title"), "cwd": row.get("directory"), "source": "opencode",
                "archived": bool(parent or row.get("revert") or (timing or {}).get("archived")),
                "updatedAt": updated / 1000 if numeric(updated) else None}

    @staticmethod
    def metadata_v2(row):
        if not isinstance(row, dict) or not valid_session(row.get("id")):
            raise BackendError("opencode_response_incompatible")
        timing = row.get("time")
        if timing is not None and not isinstance(timing, dict):
            raise BackendError("opencode_response_incompatible")
        parent = row.get("parentID")
        if parent is not None and not isinstance(parent, str):
            raise BackendError("opencode_response_incompatible")
        location = row.get("location")
        cwd = location.get("directory") if isinstance(location, dict) else None
        if cwd is not None and not isinstance(cwd, str):
            raise BackendError("opencode_response_incompatible")
        updated = (timing or {}).get("updated")
        return {"id": row["id"], "name": row.get("title"), "cwd": cwd, "source": "opencode",
                "archived": bool(parent or row.get("revert") or (timing or {}).get("archived")),
                "updatedAt": updated / 1000 if numeric(updated) else None}

    def running(self):
        """Return the exact set of sessions with an active turn."""
        self._detect()
        try:
            if self.mode == "v1":
                status = self.request("/session/status")
                if not isinstance(status, dict):
                    raise BackendError("opencode_response_incompatible")
                return {sid for sid, value in status.items()
                        if valid_session(sid) and isinstance(value, dict)
                        and value.get("type") not in (None, "idle")}
            value = self.request("/api/session/active")
        except BackendError as error:
            if str(error) in ("opencode_http_404", "opencode_http_405"):
                raise BackendError("opencode_experimental_api_missing") from None
            raise
        data = value.get("data") if isinstance(value, dict) else None
        if not isinstance(data, dict):
            raise BackendError("opencode_response_incompatible")
        return {sid for sid in data if valid_session(sid)}

    def thread(self, thread_id):
        self._detect()
        if not valid_session(thread_id):
            raise BackendError("invalid_thread_id")
        if self.mode == "v1":
            row = self.request("/session/" + thread_id)
            if not isinstance(row, dict):
                raise BackendError("opencode_response_incompatible")
            if row.get("id") != thread_id:
                raise BackendError("opencode_identity_mismatch")
            return self.metadata(row)
        value = self.request("/api/session/" + thread_id)
        row = value.get("data") if isinstance(value, dict) else None
        if not isinstance(row, dict):
            raise BackendError("opencode_response_incompatible")
        if row.get("id") != thread_id:
            raise BackendError("opencode_identity_mismatch")
        return self.metadata_v2(row)

    def latest(self, thread_id):
        self._detect()
        if not valid_session(thread_id):
            raise BackendError("invalid_thread_id")
        if self.mode == "v1":
            return self._latest_v1(thread_id)
        return self._latest_v2(thread_id)

    def _latest_v1(self, thread_id):
        status = self.request("/session/status")
        if not isinstance(status, dict):
            raise BackendError("opencode_response_incompatible")
        active = status.get(thread_id, {"type": "idle"})
        if not isinstance(active, dict):
            raise BackendError("opencode_response_incompatible")
        # OpenCode's own retry loop must finish before a second client acts.
        blocked = active.get("type") != "idle"
        for path in ("/permission", "/question"):
            try:
                pending = self.request(path)
            except BackendError as error:
                if str(error) in ("opencode_http_404", "opencode_http_405"):
                    raise BackendError("opencode_experimental_api_missing") from None
                raise
            if not isinstance(pending, list):
                raise BackendError("opencode_response_incompatible")
            for row in pending:
                if not isinstance(row, dict):
                    raise BackendError("opencode_response_incompatible")
                blocked |= row.get("sessionID") == thread_id
        rows = self.request("/session/" + thread_id + "/message", params={"limit": 1})
        if not isinstance(rows, list):
            raise BackendError("opencode_response_incompatible")
        if not rows:
            return None
        if not isinstance(rows[-1], dict):
            raise BackendError("opencode_response_incompatible")
        info = rows[-1].get("info")
        if not isinstance(info, dict):
            raise BackendError("opencode_response_incompatible")
        if info.get("sessionID") != thread_id:
            raise BackendError("opencode_identity_mismatch")
        turn = normalize(info)
        if blocked:
            turn["status"] = "inProgress"
        model = {"providerID": info.get("providerID"), "modelID": info.get("modelID")}
        if not all(isinstance(v, str) and v for v in model.values()) or not isinstance(info.get("agent"), str):
            turn["status"] = "completed"
        else:
            self.routes[thread_id] = {"model": model, "agent": info["agent"]}
            if isinstance(info.get("variant"), str):
                self.routes[thread_id]["variant"] = info["variant"]
            if valid_message(info.get("parentID")):
                parent = self.request("/session/" + thread_id + "/message/" + info["parentID"])
                if not isinstance(parent, dict) or not isinstance(parent.get("info"), dict):
                    raise BackendError("opencode_response_incompatible")
                parent = parent["info"]
                if parent.get("sessionID") != thread_id or parent.get("id") != info["parentID"] or parent.get("role") != "user":
                    raise BackendError("opencode_identity_mismatch")
                # Per-message tool restrictions and client system instructions must survive continuation.
                for key in ("tools", "system", "format"):
                    if key in parent:
                        self.routes[thread_id][key] = parent[key]
        return turn

    def _latest_v2(self, thread_id):
        try:
            active = self.request("/api/session/active")
        except BackendError as error:
            if str(error) in ("opencode_http_404", "opencode_http_405"):
                raise BackendError("opencode_experimental_api_missing") from None
            raise
        if not isinstance(active, dict) or not isinstance(active.get("data"), dict):
            raise BackendError("opencode_response_incompatible")
        blocked = thread_id in active["data"]
        params = {"location[directory]": self.directory} if self.directory else None
        try:
            pending = self.request("/api/permission/request", params=params)
        except BackendError as error:
            if str(error) in ("opencode_http_404", "opencode_http_405"):
                raise BackendError("opencode_experimental_api_missing") from None
            raise
        if not isinstance(pending, dict) or not isinstance(pending.get("data"), list):
            raise BackendError("opencode_response_incompatible")
        for row in pending["data"]:
            if not isinstance(row, dict):
                raise BackendError("opencode_response_incompatible")
            blocked |= row.get("sessionID") == thread_id
        try:
            forms = self.request("/api/session/" + thread_id + "/form")
        except BackendError as error:
            if str(error) in ("opencode_http_404", "opencode_http_405"):
                raise BackendError("opencode_experimental_api_missing") from None
            raise
        if not isinstance(forms, dict) or not isinstance(forms.get("data"), list):
            raise BackendError("opencode_response_incompatible")
        for row in forms["data"]:
            if not isinstance(row, dict):
                raise BackendError("opencode_response_incompatible")
            state = row.get("state")
            blocked |= (row.get("sessionID") == thread_id and isinstance(state, dict)
                        and state.get("status") == "pending")
        rows = self.request("/api/session/" + thread_id + "/message", params={"limit": 1, "order": "desc"})
        if not isinstance(rows, dict) or not isinstance(rows.get("data"), list):
            raise BackendError("opencode_response_incompatible")
        if not rows["data"]:
            return None
        info = rows["data"][-1]
        if not isinstance(info, dict):
            raise BackendError("opencode_response_incompatible")
        if info.get("sessionID") is not None and info["sessionID"] != thread_id:
            raise BackendError("opencode_identity_mismatch")
        turn = normalize_v2(info, go_limited=self._go_limited)
        if blocked or isinstance(info.get("retry"), dict):
            turn["status"] = "inProgress"
        self.routes[thread_id] = {"v2": True}
        return turn

    def submit(self, thread_id, message):
        self._detect()
        if not valid_session(thread_id) or thread_id not in self.routes:
            return "uncertain"
        if self.mode == "v2":
            # The 2.x prompt route keeps the session's model, agent, variant and
            # permissions. A successful response only admits the input, so a
            # transport failure stays uncertain and is never retried.
            try:
                self.request("/api/session/" + thread_id + "/prompt",
                             {"text": message, "delivery": "queue", "resume": True})
                return "accepted"
            except BackendError:
                return "uncertain"
        # A successful 204 acknowledges acceptance, not completion. Never retry an ambiguous POST.
        try:
            self.request("/session/" + thread_id + "/prompt_async", {
                **self.routes[thread_id], "parts": [{"type": "text", "text": message}]})
            return "accepted"
        except BackendError:
            return "uncertain"

    def close(self):
        pass
