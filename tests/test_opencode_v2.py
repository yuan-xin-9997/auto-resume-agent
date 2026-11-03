import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

import pytest

from auto_resume_agent.backends import selected_store
from auto_resume_agent.cli import main
from auto_resume_agent.engine import Engine
from auto_resume_agent.model import category
from auto_resume_agent.opencode import OpenCode, normalize_v2
from auto_resume_agent.protocol import BackendError
from auto_resume_agent.store import Store

SID = "ses_v2abc123"
MID = "msg_v2idle123"
NOW = 1_800_000_000


def session(**overrides):
    row = {"id": SID, "projectID": "prj_1", "title": "V2 fixture", "agent": "build",
           "model": {"id": "deepseek-v4.1-flash", "providerID": "opencode-go", "variant": "max"},
           "time": {"created": (NOW - 100) * 1000, "updated": (NOW - 10) * 1000},
           "location": {"directory": "/fixture"}}
    row.update(overrides)
    return row


def error(kind="provider.quota", status=429, body=None, retry=None):
    row = {"type": kind, "message": "PRIVATE_ERROR"}
    if status is not None:
        row["status"] = status
    if body is not None:
        row["response"] = {"body": json.dumps(body)}
    if retry is not None:
        row["retryAfterMs"] = retry
    return row


def idle(error_row=None, outcome="failed", completed=None):
    row = {"id": MID, "type": "idle", "outcome": outcome,
           "time": {"created": (NOW - 10) * 1000}}
    if completed is not None:
        row["time"]["completed"] = completed * 1000
    if error_row is not None:
        row["error"] = error_row
    return row


@pytest.fixture
def service_v2():
    state = {
        "sessions": [session()],
        "message": idle(error("provider.quota", 429, {
            "type": "error", "error": {"type": "GoUsageLimitError", "message": "Go limit reached"}})),
        "active": {},
        "permission": [],
        "form": [],
        "usage": {"go": {
            "rolling": {"percent": 4, "limited": False, "resetsAt": (NOW + 3600) * 1000},
            "weekly": {"percent": 1, "limited": False, "resetsAt": (NOW + 86400) * 1000},
            "monthly": {"percent": 0, "limited": False, "resetsAt": (NOW + 2592000) * 1000},
        }},
        "submitted": [],
        "requests": [],
        "auth": None,
        "cursor": "next-page",
        "usage_missing": False,
    }

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def response_json(self, value, status=200):
            raw = json.dumps(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def response_html(self):
            raw = b"<!doctype html><html></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def authorized(self):
            if state["auth"] and self.headers.get("Authorization") != state["auth"]:
                self.response_json({"_tag": "UnauthorizedError", "message": "Authentication required"}, 401)
                return False
            return True

        def do_GET(self):
            parsed = urlsplit(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)
            state["requests"].append((self.path, self.headers.get("Authorization")))
            if path == "/global/health":
                return self.response_html()
            if not self.authorized():
                return
            if path == "/api/session":
                following = query.get("cursor", [None])[0] is not None
                return self.response_json({"data": state["sessions"],
                                           "cursor": {"previous": None,
                                                      "next": None if following else state["cursor"]}})
            if path == "/api/session/" + SID:
                return self.response_json({"data": state["sessions"][0]})
            if path == "/api/session/active":
                return self.response_json({"data": state["active"]})
            if path == "/api/permission/request":
                return self.response_json({"location": {"directory": "/fixture"}, "data": state["permission"]})
            if path == "/api/session/" + SID + "/form":
                return self.response_json({"data": state["form"]})
            if path == "/api/session/" + SID + "/message":
                return self.response_json({"data": [state["message"]],
                                           "cursor": {"previous": None, "next": None}})
            if path == "/api/experimental/usage/limits":
                if state["usage_missing"]:
                    return self.response_json({"_tag": "NotFoundError", "message": "not found"}, 404)
                return self.response_json({"location": {"directory": "/fixture"}, "data": state["usage"]})
            return self.response_json({"_tag": "NotFoundError", "message": "not found"}, 404)

        def do_POST(self):
            path = urlsplit(self.path).path
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            state["submitted"].append((path, body))
            if not self.authorized():
                return
            if path == "/api/session/" + SID + "/prompt":
                return self.response_json({"data": {"id": "msg_inbox123", "sessionID": SID, "type": "user",
                                                    "time": {"created": NOW * 1000}, "payload": body,
                                                    "delivery": "queue"}})
            return self.response_json({"_tag": "NotFoundError", "message": "not found"}, 404)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        yield state, url
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def prepare(tmp_path, url):
    base = Store(tmp_path)
    base.set("opencode_url", url)
    base.set("opencode_directory", "/fixture")
    store = selected_store(base, "opencode")
    store.watch(SID)
    store.set("enabled", True)
    return store, OpenCode(url, "/fixture")


def test_v2_detection_sessions_pagination_and_go_usage(service_v2):
    state, url = service_v2
    backend = OpenCode(url, "/fixture")
    backend.start()
    assert backend.mode == "v2"
    page = backend.threads()
    assert page["nextCursor"] == "next-page"
    assert page["data"] == [{"id": SID, "name": "V2 fixture", "cwd": "/fixture",
                             "source": "opencode", "archived": False,
                             "updatedAt": (NOW - 10) * 1000 / 1000}]
    backend.thread(SID)
    following = backend.threads("next-page")
    assert following["nextCursor"] is None
    assert any("cursor=next-page" in request for request, _ in state["requests"])
    usage = backend.usage()
    assert usage["available"] is True and usage["reset_at"] is None
    assert [(window["window"], window["minutes"]) for window in usage["windows"]] == [
        ("rolling", 300), ("weekly", 10080), ("monthly", 43200)]
    assert usage["windows"][0]["bucket"] == "OpenCode Go"
    assert any("location%5Bdirectory%5D=%2Ffixture" in request for request, _ in state["requests"])


def test_v2_go_limit_exposes_reset(service_v2):
    state, url = service_v2
    state["usage"]["go"]["rolling"].update({"percent": 100, "limited": True,
                                            "resetsAt": (NOW + 300) * 1000})
    backend = OpenCode(url, "/fixture")
    usage = backend.usage()
    assert usage["available"] is False and usage["reset_at"] == NOW + 300
    assert backend._go_limited is True


def test_v2_usage_endpoint_missing_stays_unknown(service_v2):
    state, url = service_v2
    state["usage_missing"] = True
    usage = OpenCode(url, "/fixture").usage()
    assert usage == {"available": None, "reset_at": None, "windows": [], "reason": "quota_not_exposed"}


def test_v2_child_and_archived_sessions_are_filtered(service_v2):
    state, url = service_v2
    child = session(id="ses_v2child123", parentID=SID)
    archived = session(id="ses_v2arch123", time={"created": NOW * 1000, "updated": NOW * 1000,
                                                 "archived": NOW * 1000})
    state["sessions"] = [state["sessions"][0], child, archived]
    backend = OpenCode(url, "/fixture")
    assert [row["id"] for row in backend.threads()["data"]] == [SID]


@pytest.mark.parametrize("go_limited, expected", [
    (False, "rateLimitExceeded"),
    (True, "usageLimitExceeded"),
])
def test_v2_quota_provider_classification(go_limited, expected):
    message = {"id": MID, "type": "assistant", "finish": "error",
               "time": {"created": (NOW - 10) * 1000, "completed": (NOW - 5) * 1000},
               "agent": "build", "model": {"id": "deepseek-v4.1-flash", "providerID": "opencode-go"},
               "content": [],
               "error": error("provider.quota", 429, {
                   "type": "error", "error": {"type": "FreeUsageLimitError", "message": "limit"}})}
    turn = normalize_v2(message, go_limited)
    assert turn["status"] == "failed" and turn["error"]["codexErrorInfo"] == expected


def test_v2_go_usage_limit_error_wins():
    turn = normalize_v2(idle(error("provider.quota", 429, {
        "type": "error", "error": {"type": "GoUsageLimitError", "message": "Go limit"}})))
    assert turn["error"]["codexErrorInfo"] == "usageLimitExceeded"
    assert category(turn) == "usage_limit"


def test_v2_transient_and_terminal_errors():
    transport = normalize_v2(idle(error("provider.transport", 200)))
    assert transport["status"] == "failed" and category(transport) == "network"
    retry = normalize_v2(idle(error("provider.free-limit", 429,
                                    {"type": "error", "error": {"type": "FreeUsageLimitError"}}, retry=5000)))
    assert retry["retryAt"] == retry["completedAt"] + 5
    assert category(retry) == "rate_limit"
    server = normalize_v2(idle(error("provider.error", 503)))
    assert category(server) == "server_error"
    assert normalize_v2(idle(error("provider.error", 401)))["status"] == "completed"
    assert normalize_v2(idle(error("aborted", None), outcome="interrupted"))["status"] == "interrupted"
    assert normalize_v2(idle(error("provider.error", None)))["status"] == "completed"
    billing = normalize_v2(idle(error("provider.quota", 429, {
        "type": "error", "error": {"code": "insufficient_quota"}})))
    assert billing["status"] == "completed"
    assert normalize_v2(idle(error("provider.quota", 429, {
        "type": "error", "error": {"type": "billing_error"}})))["status"] == "completed"


@pytest.mark.parametrize("block", ["active", "permission", "form"])
def test_v2_busy_sessions_never_send(service_v2, block):
    state, url = service_v2
    if block == "active":
        state["active"] = {SID: {"type": "running"}}
    elif block == "permission":
        state["permission"] = [{"sessionID": SID}]
    else:
        state["form"] = [{"sessionID": SID, "state": {"status": "pending"}}]
    backend = OpenCode(url, "/fixture")
    assert backend.latest(SID)["status"] == "inProgress"


def test_v2_engine_waits_for_go_reset_and_submits_once(tmp_path, service_v2):
    state, url = service_v2
    state["usage"]["go"]["rolling"].update({"percent": 100, "limited": True,
                                            "resetsAt": (NOW + 300) * 1000})
    store, backend = prepare(tmp_path, url)
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    record = store.records()[0]
    assert record["state"] == "waiting" and record["due"] == NOW + 302
    assert not state["submitted"]
    engine.clock = lambda: NOW + 301
    engine.tick()
    assert not state["submitted"]
    state["usage"]["go"]["rolling"].update({"percent": 0, "limited": False})
    engine.clock = lambda: NOW + 303
    engine.tick()
    assert len(state["submitted"]) == 1
    path, body = state["submitted"][0]
    assert path == "/api/session/" + SID + "/prompt"
    assert body["delivery"] == "queue" and body["resume"] is True
    assert body["text"].startswith("Continue the unfinished work")
    assert store.records()[0]["state"] == "accepted"
    assert b"PRIVATE_ERROR" not in store.path.read_bytes()
    engine.clock = lambda: NOW + 500
    engine.tick()
    assert len(state["submitted"]) == 1
    finished = idle(outcome="succeeded")
    finished["id"] = "msg_v2done123"
    state["message"] = finished
    engine.clock = lambda: NOW + 600
    engine.tick()
    engine.clock = lambda: NOW + 720
    engine.tick()
    assert not store.watched()


def unwatched(tmp_path, url):
    base = Store(tmp_path)
    base.set("opencode_url", url)
    base.set("opencode_directory", "/fixture")
    store = selected_store(base, "opencode")
    store.set("enabled", True)
    return store, OpenCode(url, "/fixture")


def test_v2_running_session_is_adopted_automatically(tmp_path, service_v2):
    state, url = service_v2
    state["active"] = {SID: {"type": "running"}}
    state["message"] = {"id": "msg_v2run123", "type": "assistant",
                        "time": {"created": NOW * 1000}, "agent": "build",
                        "model": {"id": "deepseek-v4.1-flash", "providerID": "opencode-go"},
                        "content": []}
    store, backend = unwatched(tmp_path, url)
    result = Engine(store, backend, lambda: NOW).tick()
    assert result["error"] is None and result["watched"] == 1
    assert [row["id"] for row in store.watched()] == [SID]
    assert any(event["code"] == "auto_running" for event in store.events())


def test_v2_running_session_is_readopted_after_auto_unwatch(tmp_path, service_v2):
    state, url = service_v2
    state["active"] = {SID: {"type": "running"}}
    state["message"] = {"id": "msg_v2run123", "type": "assistant",
                        "time": {"created": NOW * 1000}, "agent": "build",
                        "model": {"id": "deepseek-v4.1-flash", "providerID": "opencode-go"},
                        "content": []}
    store, backend = unwatched(tmp_path, url)
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    assert [row["id"] for row in store.watched()] == [SID]
    state["active"] = {}
    state["message"] = idle(outcome="succeeded")
    engine.clock = lambda: NOW + 30
    engine.tick()
    assert [row["id"] for row in store.watched()] == [SID]
    engine.clock = lambda: NOW + 150
    engine.tick()
    assert not store.watched()
    state["active"] = {SID: {"type": "running"}}
    state["message"] = {"id": "msg_v2run456", "type": "assistant",
                        "time": {"created": (NOW + 170) * 1000}, "agent": "build",
                        "model": {"id": "deepseek-v4.1-flash", "providerID": "opencode-go"},
                        "content": []}
    engine.clock = lambda: NOW + 180
    engine.tick()
    assert [row["id"] for row in store.watched()] == [SID]
    assert sum(event["code"] == "auto_running" for event in store.events()) >= 2


def test_v2_active_session_survives_completed_latest_status(tmp_path, service_v2):
    state, url = service_v2
    state["active"] = {SID: {"type": "running"}}
    store, backend = unwatched(tmp_path, url)
    backend.latest = lambda tid: {"id": "msg_v2done123", "status": "completed",
                                  "completedAt": NOW * 1000}
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    assert [row["id"] for row in store.watched()] == [SID]
    engine.clock = lambda: NOW + 150
    engine.tick()
    assert [row["id"] for row in store.watched()] == [SID]


def test_v2_quota_failure_is_adopted_automatically(tmp_path, service_v2):
    _, url = service_v2
    store, backend = unwatched(tmp_path, url)
    result = Engine(store, backend, lambda: NOW).tick()
    assert result["error"] is None and result["watched"] == 1
    assert [row["id"] for row in store.watched()] == [SID]
    assert store.records()[0]["kind"] == "usage_limit"
    assert any(event["code"] == "auto_watched" for event in store.events())


def test_v2_ambiguous_prompt_is_not_repeated(tmp_path, service_v2):
    state, url = service_v2
    store, backend = prepare(tmp_path, url)
    request = backend.request

    def ambiguous(path, body=None, params=None, allow_missing=False):
        if body is not None:
            state["submitted"].append((path, body))
            raise BackendError("opencode_connection_failed")
        return request(path, body, params, allow_missing)

    backend.request = ambiguous
    engine = Engine(store, backend, lambda: NOW + 100)
    engine.tick()
    engine.clock = lambda: NOW + 1000
    engine.tick()
    assert len(state["submitted"]) == 1
    assert store.records()[0]["state"] == "uncertain"


def test_v2_auth_required_and_basic_success(tmp_path, service_v2, monkeypatch):
    state, url = service_v2
    password = "test-secret"
    monkeypatch.delenv("OPENCODE_SERVER_PASSWORD", raising=False)
    monkeypatch.setattr("auto_resume_agent.opencode.SERVICE_CONFIG", tmp_path / "missing-service.json")
    state["auth"] = "Basic " + base64.b64encode(("opencode:" + password).encode()).decode()
    with pytest.raises(BackendError) as failure:
        OpenCode(url, "/fixture").start()
    assert str(failure.value) == "opencode_auth_required"
    monkeypatch.setenv("OPENCODE_SERVER_PASSWORD", password)
    backend = OpenCode(url, "/fixture")
    backend.start()
    assert backend.threads()["data"][0]["id"] == SID
    assert any(header and header.startswith("Basic ") for _, header in state["requests"])


def test_v2_loopback_reads_desktop_service_password(tmp_path, service_v2, monkeypatch):
    state, url = service_v2
    password = "desktop-secret"
    monkeypatch.delenv("OPENCODE_SERVER_PASSWORD", raising=False)
    monkeypatch.delenv("OPENCODE_SERVER_USERNAME", raising=False)
    state["auth"] = "Basic " + base64.b64encode(("desktop:" + password).encode()).decode()
    config = tmp_path / "service.json"
    config.write_text(json.dumps({"username": "desktop", "password": password}), encoding="utf-8")
    monkeypatch.setattr("auto_resume_agent.opencode.SERVICE_CONFIG", config)
    backend = OpenCode(url, "/fixture")
    backend.start()
    assert backend.threads()["data"][0]["id"] == SID
    assert any(header and header.startswith("Basic ") for _, header in state["requests"])
    remote = OpenCode("https://example.com", "/fixture")
    assert "Authorization" not in remote._headers(None)


def test_v2_doctor_reports_known_go_quota(tmp_path, service_v2, monkeypatch, capsys):
    _, url = service_v2
    monkeypatch.setenv("OPENCODE_SERVER_PASSWORD", "test-secret")
    assert main(["--home", str(tmp_path), "--agent", "opencode", "--opencode-url", url,
                 "--opencode-directory", "/fixture", "doctor"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["compatible"] is True
    assert report["quota_known"] is True
    assert report["checks"] == {"start": "ok", "usage": "ok", "thread_list": "ok",
                                "thread_read": "ok", "latest_turn": "ok"}
