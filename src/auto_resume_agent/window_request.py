"""A separate client may start one new helper thread and its single '回复 OK' turn."""
import queue
import tempfile
import time

from .protocol import Codex, BackendError
from .store import valid_id

PROMPT = "回复 OK"
INSTRUCTIONS = "Reply exactly OK to the user. Do not inspect files, execute commands, call tools, delegate, or work on a project."


class WindowClient(Codex):
    METHODS = Codex.METHODS | {"thread/start", "thread/name/set", "turn/start"}

    def __init__(self, backend):
        super().__init__(backend.argv[0], timeout=backend.timeout)
        self.argv = list(backend.argv)
        self.owned = None
        self.creating = False
        self.started = False
        self.events = queue.Queue(maxsize=32)

    def call(self, method, params=None, initialize=False):
        if method == "thread/start":
            if self.owned is not None or self.creating:
                raise BackendError("helper_already_created")
            self.creating = True
        elif method in ("thread/name/set", "turn/start"):
            if not self.owned or (params or {}).get("threadId") != self.owned:
                raise BackendError("helper_thread_mismatch")
            if method == "turn/start":
                if self.started or (params or {}).get("input") != [{"type": "text", "text": PROMPT}]:
                    raise BackendError("helper_turn_not_allowed")
                self.started = True
        return super().call(method, params, initialize)

    def notification(self, value):
        if value.get("method") not in ("turn/completed", "item/completed"):
            return
        params = value.get("params") or {}
        if params.get("threadId") != self.owned:
            return
        try:
            self.events.put_nowait(value)
        except queue.Full:
            pass


def send(backend, on_created, can_send, wait_seconds=45):
    client = WindowClient(backend)
    workspace = None
    try:
        client.start()
        if not can_send():
            return "cancelled"
        workspace = tempfile.TemporaryDirectory(prefix="ara-window-")
        directory = workspace.name
        result = client.call("thread/start", {"cwd": directory, "sandbox": "read-only", "approvalPolicy": "never",
            "baseInstructions": INSTRUCTIONS, "developerInstructions": INSTRUCTIONS, "ephemeral": False})
        thread_id = (result.get("thread") or {}).get("id")
        if not valid_id(thread_id):
            return "uncertain"
        client.owned = thread_id
        on_created(thread_id)
        if not can_send():
            return "cancelled"
        client.call("thread/name/set", {"threadId": thread_id, "name": "Auto Resume Agent · 5h window"})
        if not can_send():
            return "cancelled"
        turn = client.call("turn/start", {"threadId": thread_id, "input": [{"type": "text", "text": PROMPT}],
                                         "approvalPolicy": "never"}).get("turn", {})
        turn_id = turn.get("id")
        end = time.monotonic() + wait_seconds
        reply_ok = False
        while time.monotonic() < end:
            try:
                event = client.events.get(timeout=max(0.01, end-time.monotonic()))
            except queue.Empty:
                break
            params = event["params"]
            if event["method"] == "item/completed" and params.get("turnId") == turn_id:
                item = params.get("item") or {}
                reply_ok |= item.get("type") == "agentMessage" and str(item.get("text", "")).strip() == "OK"
            if event["method"] == "turn/completed" and (params.get("turn") or {}).get("id") == turn_id:
                status = params["turn"].get("status")
                return "completed" if status == "completed" and reply_ok else "accepted" if status == "completed" else "failed"
        return "uncertain"
    except (BackendError, OSError, ValueError):
        return "uncertain"
    finally:
        client.close()
        if workspace:
            try:
                workspace.cleanup()
            except OSError:
                pass  # Windows may still be releasing helper files; delivery status must survive cleanup.
