import copy
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from auto_resume_agent.backends import selected_store
from auto_resume_agent.cli import main
from auto_resume_agent.engine import Engine
from auto_resume_agent.opencode import OpenCode, endpoint, normalize
from auto_resume_agent.protocol import BackendError
from auto_resume_agent.store import Store

SID = "ses_abc123"
MID = "msg_abc123"
NOW = 1_800_000_000


def assistant(status=429, retryable=True):
    return {"id": MID, "sessionID": SID, "role": "assistant", "agent": "build",
            "parentID": "msg_parent",
            "providerID": "fixture", "modelID": "original", "variant": "fast",
            "time": {"created": (NOW-30)*1000, "completed": (NOW-20)*1000},
            "error": {"name": "APIError", "data": {"message": "PRIVATE_ERROR", "statusCode": status,
                     "isRetryable": retryable, "responseHeaders": {"Retry-After": "30"}}}}


@pytest.fixture
def service():
    state = {"message": assistant(), "status": {}, "permission": [], "question": [], "submitted": [],
             "session": {"id": SID, "title": "Fixture", "directory": "/fixture", "time": {}}, "requests": []}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = self.path.split("?")[0]
            state["requests"].append((self.path, self.headers.get("Authorization")))
            values = {"/global/health": {"healthy": True, "version": "fixture"}, "/session": [state["session"]],
                      "/session/"+SID: state["session"], "/session/status": state["status"],
                      "/permission": state["permission"], "/question": state["question"],
                      "/session/"+SID+"/message": [{"info": state["message"], "parts": [{"text": "PRIVATE_TRANSCRIPT"}]}]}
            values["/session/"+SID+"/message/msg_parent"] = {"info": {"id": "msg_parent", "sessionID": SID,
                "role": "user", "tools": {"bash": False}, "system": "Keep original restrictions"}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(values[path]).encode())

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["submitted"].append((self.path, body))
            self.send_response(204)
            self.end_headers()
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
    base.set("opencode_directory", "/fixture & workspace")
    store = selected_store(base, "opencode")
    store.watch(SID)
    with store.db() as db:
        db.execute("UPDATE watched SET armed=?", (NOW-60,))
    store.set("enabled", True)
    return base, store, OpenCode(url, "/fixture & workspace")


def test_http_recovery_retry_after_identity_model_and_no_duplicate(tmp_path, service, monkeypatch):
    monkeypatch.setenv("OPENCODE_SERVER_PASSWORD", "test-secret")
    state, url = service
    base, store, backend = prepare(tmp_path, url)
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    assert store.records()[0]["due"] == NOW+10
    assert not state["submitted"]
    engine.clock = lambda: NOW+11
    engine.tick()
    assert len(state["submitted"]) == 1
    path, body = state["submitted"][0]
    assert path.startswith("/session/"+SID+"/prompt_async?")
    assert body["model"] == {"providerID": "fixture", "modelID": "original"}
    assert body["agent"] == "build" and body["variant"] == "fast"
    assert body["tools"] == {"bash": False} and body["system"] == "Keep original restrictions"
    assert store.records()[0]["state"] == "accepted"
    Engine(store, backend, lambda: NOW+100).tick()
    assert len(state["submitted"]) == 1
    assert state["requests"][0][1].startswith("Basic ")
    assert any("directory=%2Ffixture+%26+workspace" in r[0] for r in state["requests"])
    raw = store.path.read_bytes()
    assert all(x not in raw for x in (b"PRIVATE_ERROR", b"PRIVATE_TRANSCRIPT", b"test-secret"))
    assert store.get("usage")["available"] is None


@pytest.mark.parametrize("block", ["busy", "retry", "permission", "question", "archived", "child", "revert"])
def test_active_held_and_child_sessions_never_send(tmp_path, service, block):
    state, url = service
    _, store, backend = prepare(tmp_path, url)
    state["message"]["error"]["data"]["responseHeaders"] = {}
    if block in ("busy", "retry"):
        state["status"][SID] = {"type": block}
    elif block in ("permission", "question"):
        state[block] = [{"sessionID": SID}]
    elif block == "archived":
        state["session"]["time"]["archived"] = NOW
    elif block == "child":
        state["session"]["parentID"] = "ses_parent"
    else:
        state["session"]["revert"] = {"messageID": MID}
    Engine(store, backend, lambda: NOW+100).tick()
    assert not state["submitted"]


@pytest.mark.parametrize("code", [400, 401, 402, 403, 404, 409, 422])
def test_terminal_http_codes(code):
    assert normalize(assistant(code))["status"] != "failed"


@pytest.mark.parametrize("name", ["MessageAbortedError", "ProviderAuthError", "ContextOverflowError", "UnknownError"])
def test_terminal_error_names(name):
    row = assistant()
    row["error"]["name"] = name
    assert normalize(row)["status"] != "failed"


def test_billing_denial_not_rate_limit():
    row = assistant()
    row["error"]["data"]["responseBody"] = json.dumps({"error": {"code": "insufficient_quota"}})
    assert normalize(row)["status"] != "failed"
    assert normalize(assistant(429, False))["status"] != "failed"
    assert normalize(assistant(503))["status"] == "failed"


def test_identity_url_and_store_isolation(tmp_path, service):
    _, url = service
    base, store, _ = prepare(tmp_path, url)
    assert not base.watched()
    base.set("opencode_directory", "/other")
    other = selected_store(base, "opencode")
    assert not other.watched() and other.root != store.root
    with pytest.raises(ValueError):
        base.watch(SID)
    with pytest.raises(ValueError):
        store.watch("../injection")
    for value in ("http://example.com", "https://user:pass@example.com", "file:///tmp", "http://localhost:4096/path"):
        with pytest.raises(BackendError):
            endpoint(value)


def test_ambiguous_post_never_repeated(tmp_path, service):
    state, url = service
    _, store, backend = prepare(tmp_path, url)
    state["message"]["error"]["data"]["responseHeaders"] = {}
    request = backend.request
    def ambiguous(path, body=None, params=None):
        if body is not None:
            state["submitted"].append((path, body))
            raise BackendError("opencode_connection_failed")
        return request(path, body, params)
    backend.request = ambiguous
    Engine(store, backend, lambda: NOW+100).tick()
    Engine(store, backend, lambda: NOW+1000).tick()
    assert len(state["submitted"]) == 1
    assert store.records()[0]["state"] == "uncertain"


def test_new_user_message_supersedes(tmp_path, service):
    state, url = service
    _, store, backend = prepare(tmp_path, url)
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    state["message"] = {"id": "msg_newuser", "sessionID": SID, "role": "user", "time": {"created": NOW*1000}}
    engine.clock = lambda: NOW+100
    engine.tick()
    assert store.records()[0]["state"] == "superseded"
    assert not state["submitted"]


def test_cancellation_of_waiting_failure_stops_recovery(tmp_path, service):
    state, url = service
    _, store, backend = prepare(tmp_path, url)
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    state["message"]["error"]["name"] = "MessageAbortedError"
    engine.clock = lambda: NOW+100
    engine.tick()
    assert store.records()[0]["state"] == "superseded"
    assert not state["submitted"]


def test_cli_doctor_and_usage_without_codex(tmp_path, service, capsys):
    _, url = service
    args = ["--home", str(tmp_path), "--agent", "opencode", "--opencode-url", url]
    assert main(args+["doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["quota_known"] is False
    assert main(args+["usage"]) == 0
    assert json.loads(capsys.readouterr().out)["reason"] == "quota_not_exposed"
