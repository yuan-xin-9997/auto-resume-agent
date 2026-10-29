import contextlib
import copy
import json
import uuid

import pytest

from auto_resume_agent.engine import Engine
from auto_resume_agent.model import usage, category, next_delay
from auto_resume_agent.store import Store, engine_lock
from auto_resume_agent.protocol import BackendError, Codex

TID = str(uuid.uuid4())
TURN = str(uuid.uuid4())
NOW = 1_800_000_000


def quota(used=20, reset=NOW + 100):
    return {"rateLimits": {"primary": {"usedPercent": used, "resetsAt": reset, "windowDurationMins": 300}}}


class FakeCodex:
    def __init__(self):
        self.turn = {"id": TURN, "status": "failed", "completedAt": NOW-20,
                     "error": {"codexErrorInfo": "usageLimitExceeded"}}
        self.quota = quota()
        self.sent = []
        self.result = "queued"

    def usage(self):
        return copy.deepcopy(self.quota)

    def thread(self, tid):
        return {"id": tid, "source": "appServer", "archived": False}

    def latest(self, tid):
        return copy.deepcopy(self.turn)

    def submit(self, tid, message):
        self.sent.append((tid, message))
        return self.result


@pytest.fixture
def system(tmp_path):
    store = Store(tmp_path)
    store.watch(TID)
    with store.db() as db:
        db.execute("UPDATE watched SET armed=?", (NOW-60,))
    store.set("enabled", True)
    backend = FakeCodex()
    engine = Engine(store, backend, lambda: NOW)
    return store, backend, engine


def test_exact_uuid_once_even_after_restart(system):
    store, backend, engine = system
    engine.tick()
    assert backend.sent[0][0] == TID
    assert len(backend.sent) == 1
    assert store.records()[0]["state"] == "queued"
    Engine(store, backend, lambda: NOW+500).tick()
    assert len(backend.sent) == 1


def test_no_submission_in_observe_mode(system):
    store, backend, engine = system
    store.set("enabled", False)
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["state"] == "waiting"


def test_watch_includes_latest_failure_older_than_one_minute(system):
    store, backend, engine = system
    backend.turn["completedAt"] = NOW-7200
    engine.tick()
    assert len(backend.sent) == 1 and backend.sent[0][0] == TID
    Engine(store, backend, lambda: NOW+500).tick()
    assert len(backend.sent) == 1


def test_old_cancelled_failure_is_not_revived_by_watch(system):
    store, backend, engine = system
    backend.turn["completedAt"] = NOW-7200
    store.set("enabled", False)
    engine.tick()
    store.unwatch(TID)
    store.watch(TID)
    store.set("enabled", True)
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["state"] == "cancelled"


def test_wait_until_latest_exhausted_window_resets_then_refresh(system):
    store, backend, engine = system
    backend.quota = {"rateLimitsByLimitId": {
        "codex": {"primary": {"usedPercent": 100, "resetsAt": NOW+100},
                  "secondary": {"usedPercent": 100, "resetsAt": NOW+900}}}}
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["due"] == NOW+902
    # Sleep/wake crosses the reset. A fresh live usage reply, not wall time alone, authorizes sending.
    backend.quota = quota()
    engine.clock = lambda: NOW+903
    engine.tick()
    assert len(backend.sent) == 1


def test_stale_exhausted_quota_does_not_authorize(system):
    store, backend, engine = system
    backend.quota = quota(100, NOW-10)
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["state"] == "waiting"


def test_new_turn_supersedes(system):
    store, backend, engine = system
    store.set("enabled", False)
    engine.tick()
    backend.turn = {"id": str(uuid.uuid4()), "status": "inProgress"}
    store.set("enabled", True)
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["state"] == "superseded"


def test_timeout_never_resubmits(system):
    store, backend, engine = system
    backend.result = "uncertain"
    engine.tick()
    Engine(store, backend, lambda: NOW+1000).tick()
    assert len(backend.sent) == 1
    assert store.records()[0]["state"] == "uncertain"


def test_crash_after_claim_never_resubmits(system):
    store, backend, engine = system
    def crash(*args):
        raise RuntimeError("simulated crash")
    backend.submit = crash
    with pytest.raises(RuntimeError):
        engine.tick()
    assert store.records()[0]["state"] == "sending"
    backend.submit = lambda *args: pytest.fail("must not resend")
    Engine(store, backend, lambda: NOW+1000).tick()
    assert store.records()[0]["state"] == "uncertain"


@pytest.mark.parametrize("code", ["unauthorized", "badRequest", "contextWindowExceeded", "sandboxError", "futureCode"])
def test_terminal_and_unknown_errors_never_send(system, code):
    store, backend, engine = system
    backend.turn["error"]["codexErrorInfo"] = code
    engine.tick()
    assert not backend.sent


def test_user_cancellation_never_sends(system):
    store, backend, engine = system
    backend.turn["status"] = "interrupted"
    engine.tick()
    assert not backend.sent


def test_duplicate_instances_hold_same_lock(system):
    store, backend, engine = system
    with engine_lock(store.root) as acquired:
        assert acquired
        assert engine.tick()["error"] == "another_monitor"
    engine.tick()
    assert len(backend.sent) == 1


def test_user_progress_cannot_be_claimed_as_delivery_confirmation(system):
    store, backend, engine = system
    engine.tick()
    backend.turn = {"id": str(uuid.uuid4()), "status": "completed"}
    engine.tick()
    assert store.records()[0]["state"] == "progressed"


def test_queued_interrupted_placeholder_is_not_execution_progress(system):
    store, backend, engine = system
    engine.tick()
    backend.turn = {"id": str(uuid.uuid4()), "status": "interrupted"}
    engine.tick()
    assert store.records()[0]["state"] == "queued"
    assert len(backend.sent) == 1


def test_hourly_retry_budget(system):
    store, backend, engine = system
    for index in range(6):
        backend.turn["id"] = str(uuid.uuid4())
        backend.turn["completedAt"] = NOW+index*500-20
        engine.clock = lambda i=index: NOW+i*500+400
        engine.tick()
    assert len(backend.sent) == 5
    assert store.records()[0]["state"] == "attention"


@pytest.mark.parametrize("raw", [{}, None, {"rateLimits": {"primary": {"usedPercent": float("nan")}}},
    {"rateLimits": {"primary": {"usedPercent": True}}}, {"rateLimitsByLimitId": {"premium": None}}])
def test_invalid_usage_unknown(raw):
    assert usage(raw)["available"] is None


def test_credits_and_multiple_buckets():
    raw = quota()
    raw["rateLimits"]["spendControlReached"] = True
    assert usage(raw)["available"] is False
    assert usage(raw)["reset_at"] is None
    assert usage({"rateLimitsByLimitId": {"codex": quota()["rateLimits"], "premium": None}})["available"] is None
    raw = quota()
    raw["ordinaryUsageAllowed"] = False
    assert usage(raw)["available"] is False


def test_nested_http_errors():
    turn = {"status": "failed", "error": {"codexErrorInfo": {"httpConnectionFailed": {"httpStatusCode": 401}}}}
    assert category(turn) is None
    turn["error"]["codexErrorInfo"]["httpConnectionFailed"]["httpStatusCode"] = 503
    assert category(turn) == "network"
    assert next_delay(NOW, NOW+1) == 1
    assert next_delay(NOW+200, NOW+1) == 0.25


def test_no_transcripts_or_credentials_persisted(system):
    store, backend, engine = system
    backend.turn["error"]["message"] = "TOP_SECRET"
    backend.quota["email"] = "private@example.invalid"
    engine.tick()
    raw = store.path.read_bytes()
    assert b"TOP_SECRET" not in raw and b"private@example.invalid" not in raw


def test_protocol_write_method_rejected():
    backend = object.__new__(Codex)
    with pytest.raises(BackendError):
        backend.call("turn/start")


def test_unknown_window_keeps_whole_quota_snapshot_unknown(system):
    store, backend, engine = system
    backend.quota = {"rateLimitsByLimitId": {"codex": {
        "primary": {"usedPercent": 100, "resetsAt": NOW+100},
        "secondary": {"usedPercent": "not-a-number", "resetsAt": NOW+900}}}}
    assert usage(backend.quota)["available"] is False
    assert usage(backend.quota)["reset_at"] is None
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["state"] == "waiting"
    assert store.records()[0]["detail"] == "quota_unknown"


def test_latest_turn_change_before_claim_supersedes(system):
    store, backend, engine = system
    store.set("enabled", False)
    engine.tick()
    store.set("enabled", True)
    original = backend.latest
    calls = {"count": 0}
    newer = {"id": str(uuid.uuid4()), "status": "inProgress"}

    def latest(tid):
        calls["count"] += 1
        return copy.deepcopy(newer) if calls["count"] >= 2 else original(tid)

    backend.latest = latest
    engine.tick()
    assert not backend.sent
    assert store.records()[0]["state"] == "superseded"


def test_interface_incompatibility_blocks_all_sends(system):
    store, backend, engine = system
    second = str(uuid.uuid4())
    store.watch(second)

    def thread(tid):
        if tid == TID:
            raise BackendError("codex_experimental_api_missing")
        return {"id": tid, "source": "appServer", "archived": False}

    backend.thread = thread
    result = engine.tick()
    assert result["error"] == "codex_experimental_api_missing"
    assert not backend.sent


def test_pause_after_claim_prevents_submit(system):
    store, backend, engine = system
    original_db = store.db
    paused = {"done": False}

    @contextlib.contextmanager
    def db():
        with original_db() as connection:
            yield connection
        if not paused["done"]:
            with original_db() as check:
                row = check.execute("SELECT state FROM recoveries ORDER BY created DESC LIMIT 1").fetchone()
            if row and row["state"] == "sending":
                paused["done"] = True
                store.set("enabled", False)

    store.db = db
    engine.tick()
    assert paused["done"]
    assert not backend.sent
    assert store.records()[0]["state"] == "cancelled"


def test_cancel_or_unwatch_cancels_claimed_record(system):
    store, backend, engine = system
    store.set("enabled", False)
    engine.tick()
    record = store.records()[0]
    with store.db() as db:
        db.execute("UPDATE recoveries SET state='sending' WHERE id=?", (record["id"],))
    assert store.cancel(record["id"]) is True
    assert store.records()[0]["state"] == "cancelled"

    with store.db() as db:
        db.execute("UPDATE recoveries SET state='sending' WHERE id=?", (record["id"],))
    store.unwatch(TID)
    assert store.records()[0]["state"] == "cancelled"
    store.set("enabled", True)
    engine.tick()
    assert not backend.sent
