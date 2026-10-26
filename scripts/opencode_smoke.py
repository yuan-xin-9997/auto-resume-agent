"""End-to-end recovery with real OpenCode and an isolated, local fixture provider.

No real provider credentials are used. Run with --executable /path/to/opencode.
"""
import argparse
import json
import os
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from auto_resume_agent.backends import selected_store
from auto_resume_agent.engine import Engine
from auto_resume_agent.opencode import OpenCode
from auto_resume_agent.protocol import NO_WINDOW, external_environment, external_spawn
from auto_resume_agent.store import Store


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True)
    args = parser.parse_args()
    calls = []
    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            now = int(time.time())
            if calls[-1].get("stream"):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for delta, finish in [({"role": "assistant", "content": "ARA_RECOVERED"}, None), ({}, "stop")]:
                    payload = {"id": "chatcmpl-fixture", "object": "chat.completion.chunk", "created": now,
                               "model": "smoke", "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
                    self.wfile.write(("data: " + json.dumps(payload) + "\n\n").encode())
                self.wfile.write(b"data: [DONE]\n\n")
            else:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"id": "chatcmpl-fixture", "object": "chat.completion", "created": now,
                    "model": "smoke", "choices": [{"index": 0, "message": {"role": "assistant", "content": "ARA_RECOVERED"},
                    "finish_reason": "stop"}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}).encode())

    provider = ThreadingHTTPServer(("127.0.0.1", 0), Provider)
    threading.Thread(target=provider.serve_forever, daemon=True).start()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    server = None
    try:
        with tempfile.TemporaryDirectory(prefix="ara-opencode-smoke-") as folder:
            root = Path(folder)
            env = external_environment()
            for key in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
                env[key] = str(root / key)
            for key in ("OPENCODE_CONFIG", "OPENCODE_CONFIG_DIR", "OPENCODE_SERVER_PASSWORD", "OPENCODE_SERVER_USERNAME"):
                env.pop(key, None)
            env["OPENCODE_CONFIG_CONTENT"] = json.dumps({"permission": "deny", "enabled_providers": ["ara-fixture"],
                "model": "ara-fixture/smoke", "small_model": "ara-fixture/smoke", "provider": {"ara-fixture": {
                "npm": "@ai-sdk/openai-compatible", "name": "Local fixture", "options": {
                "baseURL": f"http://127.0.0.1:{provider.server_port}/v1", "apiKey": "fixture-not-a-secret"},
                "models": {"smoke": {"name": "Fixture"}}}}})
            with external_spawn():
                server = subprocess.Popen([args.executable, "serve", "--pure", "--hostname", "127.0.0.1", "--port", str(port)],
                    cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, creationflags=NO_WINDOW)
            backend = OpenCode(f"http://127.0.0.1:{port}", str(root), timeout=5)
            # Test server deliberately has no auth; do not inherit auth from the developer's monitor.
            original_auth = {k: os.environ.pop(k, None) for k in ("OPENCODE_SERVER_PASSWORD", "OPENCODE_SERVER_USERNAME")}
            try:
                for _ in range(60):
                    try:
                        backend.start()
                        break
                    except Exception:
                        time.sleep(1)
                else:
                    raise RuntimeError("OpenCode did not start")
                session = backend.request("/session", {"title": "ARA isolated recovery fixture"})
                sid = session["id"]
                now = int(time.time()*1000)
                user = {"id": "msg_0000000000user", "sessionID": sid, "role": "user", "time": {"created": now-25000},
                        "agent": "build", "model": {"providerID": "ara-fixture", "modelID": "smoke"}}
                assistant = {"id": "msg_0000000001assistant", "sessionID": sid, "role": "assistant",
                    "time": {"created": now-24000, "completed": now-20000}, "parentID": user["id"],
                    "agent": "build", "mode": "build", "providerID": "ara-fixture", "modelID": "smoke",
                    "path": {"cwd": str(root), "root": str(root)}, "cost": 0,
                    "tokens": {"input": 0, "output": 0, "reasoning": 0, "cache": {"read": 0, "write": 0}},
                    "error": {"name": "APIError", "data": {"message": "fixture interruption", "statusCode": 503, "isRetryable": True}}}
                fixture = root / "fixture.json"
                fixture.write_text(json.dumps({"info": session, "messages": [
                    {"info": user, "parts": [{"id": "prt_fixture", "sessionID": sid, "messageID": user["id"],
                                              "type": "text", "text": "Reply ARA_RECOVERED without using tools."}]},
                    {"info": assistant, "parts": []}]}), encoding="utf-8")
                subprocess.run([args.executable, "import", str(fixture)], cwd=root, env=env,
                               capture_output=True, check=True, timeout=30, creationflags=NO_WINDOW)
                assert backend.latest(sid)["status"] == "failed", "Imported failure was not recognized"
                base = Store(root / "monitor")
                base.set("opencode_url", backend.url)
                base.set("opencode_directory", str(root))
                store = selected_store(base, "opencode")
                store.watch(sid)
                store.set("enabled", True)
                engine = Engine(store, backend)
                engine.tick()
                assert store.records()[0]["state"] == "accepted", store.records()
                for _ in range(90):
                    rows = backend.request("/session/" + sid + "/message")
                    found = any(r["info"].get("role") == "assistant" and r["info"].get("finish") == "stop"
                                and any("ARA_RECOVERED" in p.get("text", "") for p in r.get("parts", [])) for r in rows)
                    if found:
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("Fixture provider did not complete recovery; no real provider was contacted")
                engine.tick()
                assert store.records()[0]["state"] == "progressed"
                assert len([r for r in rows if r["info"].get("role") == "user"]) == 2
                print(json.dumps({"real_opencode": True, "local_fixture_provider": True, "same_session": True,
                                  "accepted_then_completed": True, "duplicate_user_messages": False,
                                  "provider_requests": len(calls)}))
            finally:
                for key, value in original_auth.items():
                    if value is not None:
                        os.environ[key] = value
                server.terminate()
                server.wait(timeout=10)
                server = None
    finally:
        if server:
            server.kill()
            server.wait()
        provider.shutdown()
        provider.server_close()


if __name__ == "__main__":
    main()
