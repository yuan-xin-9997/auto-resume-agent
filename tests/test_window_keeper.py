import copy
import json
import sys
import uuid

import pytest

from auto_resume_agent import window_keeper as keeper
from auto_resume_agent.engine import Engine
from auto_resume_agent.cli import main
from auto_resume_agent.store import Store, engine_lock
from auto_resume_agent.protocol import Codex, BackendError
from auto_resume_agent.window_request import WindowClient, send, PROMPT

NOW = 1_800_000_000
RESET = NOW + 100


def quota(reset=RESET, used=100, available=True):
    return {"available": available, "reset_at": None, "windows": [
        {"bucket": "codex", "window": "primary", "minutes": 300, "used_percent": used, "reset_at": reset}]}


class Backend:
    def __init__(self):
        self.started = []
        self.result = "completed"

    def activate_window(self, on_created, can_send):
        assert can_send()
        tid = str(uuid.uuid4())
        self.started.append(tid)
        on_created(tid)
        return self.result


@pytest.fixture
def system(tmp_path):
    store = Store(tmp_path)
    return store, Backend()


def test_default_off_never_sends(system):
    store, backend = system
    assert not keeper.status(store)["enabled"]
    keeper.tick(store, backend, quota(NOW-10), NOW)
    assert not backend.started


def test_exhausted_quota_starts_exactly_one_new_session_at_boundary(system):
    store, backend = system
    keeper.set_enabled(store, True)
    keeper.tick(store, backend, quota(used=100), NOW)
    keeper.tick(store, backend, quota(used=100), RESET+1)
    assert not backend.started
    keeper.tick(store, backend, quota(used=0), RESET+2)
    assert len(backend.started) == 1
    assert keeper.status(store)["last_attempt"]["thread_id"] == backend.started[0]
    # Restart, disable and re-enable do not duplicate this already claimed window.
    keeper.set_enabled(store, False)
    keeper.set_enabled(store, True)
    keeper.tick(Store(store.root), backend, quota(), RESET+200)
    assert len(backend.started) == 1


def test_already_started_server_window_skips_helper(system):
    store, backend = system
    keeper.set_enabled(store, True)
    keeper.tick(store, backend, quota(), NOW)
    keeper.tick(store, backend, quota(RESET+keeper.HOURS), RESET+2)
    assert not backend.started
    assert keeper.status(store)["next_at"] == RESET + keeper.HOURS
    keeper.tick(Store(store.root), backend, quota(RESET+keeper.HOURS), RESET+100)
    assert not backend.started
    keeper.tick(store, backend, quota(RESET+keeper.HOURS), RESET+keeper.HOURS+2)
    assert len(backend.started) == 1


def test_tracks_reported_next_window_and_catches_sleep_once(system):
    store, backend = system
    keeper.set_enabled(store, True)
    keeper.tick(store, backend, quota(), NOW)
    # The monitor was asleep through two boundaries: one request, no catch-up burst.
    wake = RESET + keeper.HOURS*2
    keeper.tick(store, backend, quota(), wake)
    assert len(backend.started) == 1
    next_reset = wake + keeper.HOURS
    keeper.tick(store, backend, quota(next_reset), wake+3)
    assert keeper.status(store)["next_at"] == next_reset
    keeper.tick(store, backend, quota(next_reset), next_reset+2)
    assert len(backend.started) == 2 and backend.started[0] != backend.started[1]


@pytest.mark.parametrize("available", [False, None])
def test_weekly_block_or_unknown_quota_waits(system, available):
    store, backend = system
    keeper.set_enabled(store, True)
    keeper.tick(store, backend, quota(NOW-10, available=available), NOW)
    assert not backend.started
    keeper.tick(store, backend, quota(NOW-10), NOW+30)
    assert len(backend.started) == 1


def test_unknown_window_duration_or_reset_never_guessed(system):
    store, backend = system
    keeper.set_enabled(store, True)
    for field, value in [("minutes", None), ("minutes", 10080), ("reset_at", None), ("bucket", "premium")]:
        raw = quota(NOW-10)
        raw["windows"][0][field] = value
        keeper.tick(store, backend, raw, NOW)
    assert not backend.started


@pytest.mark.parametrize("outcome", ["accepted", "failed", "uncertain"])
def test_ambiguous_or_failed_request_is_never_retried(system, outcome):
    store, backend = system
    keeper.set_enabled(store, True)
    backend.result = outcome
    keeper.tick(store, backend, quota(NOW-10), NOW)
    keeper.tick(store, backend, quota(NOW-10), NOW+1000)
    assert len(backend.started) == 1
    assert keeper.status(store)["last_attempt"]["state"] == outcome


def test_crash_after_intent_is_not_replayed(system):
    store, backend = system
    keeper.set_enabled(store, True)
    def crash(*_):
        raise RuntimeError("fixture crash")
    backend.activate_window = crash
    with pytest.raises(RuntimeError):
        keeper.tick(store, backend, quota(NOW-10), NOW)
    assert keeper.status(store)["last_attempt"]["state"] == "uncertain"
    backend.activate_window = lambda *_: pytest.fail("must not replay")
    keeper.tick(store, backend, quota(NOW-10), NOW+1000)


def test_disable_home_isolation_and_five_hour_spacing(system):
    store, backend = system
    keeper.set_enabled(store, True)
    keeper.tick(store, backend, quota(NOW-10), NOW)
    keeper.tick(store, backend, quota(NOW+100), NOW+1)
    keeper.tick(store, backend, quota(NOW+100), NOW+102)
    assert len(backend.started) == 1
    other = Store(store.root, source="another-codex-home")
    assert not keeper.enabled(other)
    keeper.set_enabled(store, False)
    keeper.tick(store, backend, quota(NOW+100), NOW+keeper.HOURS+200)
    assert len(backend.started) == 1


def test_cli_opt_in_status_off_and_opencode_rejection(tmp_path, capsys):
    args = ["--home", str(tmp_path)]
    assert main(args+["window-keeper", "status"]) == 0
    assert json.loads(capsys.readouterr().out)["enabled"] is False
    assert main(args+["window-keeper", "on"]) == 0
    assert json.loads(capsys.readouterr().out)["enabled"] is True
    assert main(args+["window-keeper", "off"]) == 0
    assert json.loads(capsys.readouterr().out)["enabled"] is False
    with pytest.raises(SystemExit):
        main(args+["--agent", "opencode", "window-keeper", "on"])


def test_engine_independent_from_recovery_and_deadline_refresh(tmp_path):
    store = Store(tmp_path)
    keeper.set_enabled(store, True)
    store.set("enabled", False)
    class Fake(Backend):
        def __init__(self):
            super().__init__()
            self.reads = 0
        def usage(self):
            self.reads += 1
            return {"rateLimits": {"primary": {"usedPercent": 100 if self.reads == 1 else 0, "windowDurationMins": 300, "resetsAt": RESET}}}
    backend = Fake()
    engine = Engine(store, backend, lambda: RESET-1)
    engine.tick()
    assert not backend.started
    engine.clock = lambda: RESET+2
    engine.tick()
    assert backend.reads == 2 and len(backend.started) == 1
    assert store.get("enabled", False) is False
    with engine_lock(store.root) as owned:
        assert owned
        assert engine.tick()["error"] == "another_monitor"


def test_write_client_rejects_foreign_threads_and_multiple_turns():
    client = WindowClient(Codex(sys.executable))
    with pytest.raises(BackendError):
        client.call("turn/start", {"threadId": str(uuid.uuid4()), "input": []})
    client.owned = str(uuid.uuid4())
    with pytest.raises(BackendError):
        client.call("turn/start", {"threadId": client.owned, "input": [{"type": "text", "text": "wrong"}]})
    client.started = True
    with pytest.raises(BackendError):
        client.call("turn/start", {"threadId": client.owned, "input": [{"type": "text", "text": PROMPT}]})
    assert "turn/start" not in Codex.METHODS


@pytest.mark.parametrize("mode", ["success", "disable", "timeout"])
def test_real_rpc_boundary_one_new_thread_exact_prompt_and_ok(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    tid, turn = str(uuid.uuid4()), str(uuid.uuid4())
    log = tmp_path / "rpc.jsonl"
    script = tmp_path / "fixture.py"
    script.write_text('''import json,sys
from pathlib import Path
log=Path(sys.argv[1]); tid=sys.argv[2]; turn=sys.argv[3]
for line in sys.stdin:
 v=json.loads(line)
 if "id" not in v: continue
 with log.open("a",encoding="utf-8") as f: f.write(json.dumps(v)+"\\n")
 m=v["method"]
 result={"thread":{"id":tid}} if m=="thread/start" else {"turn":{"id":turn}} if m=="turn/start" else {}
 print(json.dumps({"id":v["id"],"result":result}),flush=True)
 if m=="turn/start" and sys.argv[4]=="success":
  print(json.dumps({"method":"item/completed","params":{"threadId":tid,"turnId":turn,"item":{"type":"agentMessage","text":"OK"}}}),flush=True)
  print(json.dumps({"method":"turn/completed","params":{"threadId":tid,"turn":{"id":turn,"status":"completed"}}}),flush=True)
''', encoding="utf-8")
    backend = Codex(sys.executable, timeout=2)
    backend.argv = [sys.executable, str(script), str(log), tid, turn, mode]
    created = []
    checks = iter([True, False])
    allowed = (lambda: next(checks)) if mode == "disable" else lambda: True
    expected = {"success": "completed", "disable": "cancelled", "timeout": "uncertain"}[mode]
    assert send(backend, created.append, allowed, wait_seconds=0.1 if mode == "timeout" else 2) == expected
    rows = [json.loads(v) for v in log.read_text().splitlines()]
    assert created == [tid]
    start = next(r for r in rows if r["method"] == "thread/start")
    assert start["params"]["sandbox"] == "read-only"
    assert start["params"]["ephemeral"] is False
    turns = [r for r in rows if r["method"] == "turn/start"]
    if mode == "disable":
        assert not turns
    else:
        assert len(turns) == 1 and turns[0]["params"]["input"] == [{"type": "text", "text": "回复 OK"}]
