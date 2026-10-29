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

    def request(self, path, body=None, params=None):
        query = dict(params or {})
        if self.directory:
            query["directory"] = self.directory
        url = self.url + path + ("?" + urllib.parse.urlencode(query) if query else "")
        headers = {"Accept": "application/json"}
        password = os.environ.get("OPENCODE_SERVER_PASSWORD")
        if password:
            credentials = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode") + ":" + password
            headers["Authorization"] = "Basic " + base64.b64encode(credentials.encode()).decode()
        data = json.dumps(body).encode() if body is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        try:
            with self.opener.open(urllib.request.Request(url, data=data, headers=headers), timeout=self.timeout) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
                if len(raw) > 16 * 1024 * 1024:
                    raise BackendError("opencode_response_too_large")
        except urllib.error.HTTPError as error:
            raise BackendError("opencode_http_" + str(error.code)) from None
        except (OSError, urllib.error.URLError, http.client.HTTPException):
            raise BackendError("opencode_connection_failed") from None
        try:
            return json.loads(raw) if raw else None
        except (ValueError, UnicodeDecodeError):
            raise BackendError("opencode_invalid_response") from None

    def start(self):
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
        return {"available": None, "reset_at": None, "windows": [], "reason": "quota_not_exposed"}

    def threads(self, cursor=None):
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
        return {"id": row["id"], "name": row.get("title"), "cwd": row.get("directory"), "source": "opencode",
                "archived": bool(parent or row.get("revert") or (timing or {}).get("archived"))}

    def thread(self, thread_id):
        if not valid_session(thread_id):
            raise BackendError("invalid_thread_id")
        row = self.request("/session/" + thread_id)
        if not isinstance(row, dict):
            raise BackendError("opencode_response_incompatible")
        if row.get("id") != thread_id:
            raise BackendError("opencode_identity_mismatch")
        return self.metadata(row)

    def latest(self, thread_id):
        if not valid_session(thread_id):
            raise BackendError("invalid_thread_id")
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

    def submit(self, thread_id, message):
        if not valid_session(thread_id) or thread_id not in self.routes:
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
