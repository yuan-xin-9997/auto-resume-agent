import copy
import uuid

import pytest

from auto_resume_agent.cli import main
from auto_resume_agent.discovery import QuotaDiscovery
from auto_resume_agent.engine import Engine
from auto_resume_agent.protocol import BackendError
from auto_resume_agent.store import Store

NOW = 1_800_000_000


class Backend:
    def __init__(self, count=1):
        self.rows = [{"id": str(uuid.uuid4()), "source": "vscode", "updatedAt": NOW} for _ in range(count)]
        self.turns = {r["id"]: {"id": str(uuid.uuid4()), "status": "failed", "completedAt": NOW-7200,
                               "error": {"codexErrorInfo": "usageLimitExceeded"}} for r in self.rows}
        self.reads, self.pages, self.sent = [], [], []
        self.used = 100

    def threads(self, cursor=None):
        self.pages.append(cursor)
        return {"data": self.rows, "nextCursor": None}

    def latest(self, tid):
        self.reads.append(tid)
        return copy.deepcopy(self.turns[tid])

    def thread(self, tid):
        return next(r for r in self.rows if r["id"] == tid)

    def usage(self):
        return {"rateLimits": {"primary": {"usedPercent": self.used, "resetsAt": NOW+60}}}

    def submit(self, tid, message):
        self.sent.append(tid)
        return "queued"


def test_default_discovery_watches_without_enabling_recovery(tmp_path):
    store, backend = Store(tmp_path), Backend()
    engine = Engine(store, backend, lambda: NOW)
    engine.tick()
    assert [r["id"] for r in store.watched()] == [backend.rows[0]["id"]]
    assert not store.get("enabled", False) and not backend.sent
    assert store.records()[0]["state"] == "waiting"
    assert any(r["code"] == "auto_watched" for r in store.events())
    backend.used = 10
    store.set("enabled", True)
    engine.clock = lambda: NOW+70
    engine.tick()
    engine.tick()
    assert backend.sent == [backend.rows[0]["id"]]


@pytest.mark.parametrize("case", ["completed", "interrupted", "inProgress", "network", "archived", "subagent", "helper"])
def test_only_latest_quota_failure_is_discovered(tmp_path, case):
    store, backend = Store(tmp_path), Backend()
    row = backend.rows[0]
    if case in ("completed", "interrupted", "inProgress"):
        backend.turns[row["id"]]["status"] = case
    elif case == "network":
        backend.turns[row["id"]]["error"]["codexErrorInfo"] = "httpConnectionFailed"
    elif case == "archived":
        row["archived"] = True
    elif case == "subagent":
        row["source"] = {"subagent": {}}
    else:
        row["name"] = "Auto Resume Agent · 5h window"
    QuotaDiscovery().scan(store, backend, NOW)
    assert not store.watched()


def test_manual_opt_out_survives_restart_and_manual_watch_overrides_it(tmp_path):
    store, backend = Store(tmp_path), Backend()
    tid = backend.rows[0]["id"]
    scan = QuotaDiscovery()
    scan.scan(store, backend, NOW)
    store.unwatch(tid)
    restarted = Store(tmp_path)
    QuotaDiscovery().scan(restarted, backend, NOW+40)
    assert not restarted.watched()
    restarted.watch(tid)
    assert restarted.watched()[0]["id"] == tid
    with restarted.db() as db:
        assert not db.execute("SELECT * FROM watch_exclusions WHERE id=?", (tid,)).fetchall()


def test_disabled_discovery_and_cli_controls(tmp_path, capsys):
    store, backend = Store(tmp_path), Backend()
    args = ["--home", str(tmp_path), "auto-watch"]
    assert main(args+["status"]) == 0 and 'true' in capsys.readouterr().out
    assert main(args+["off"]) == 0
    QuotaDiscovery().scan(store, backend, NOW)
    assert not backend.pages and not store.watched()
    assert store.watch(backend.rows[0]["id"], automatic=True) is False
    assert main(args+["on"]) == 0
    QuotaDiscovery().scan(store, backend, NOW)
    assert len(store.watched()) == 1


def test_bounded_paging_and_changed_head_priority(tmp_path):
    store, backend = Store(tmp_path), Backend(13)
    for t in backend.turns.values():
        t["status"] = "completed"
    def pages(cursor=None):
        backend.pages.append(cursor)
        return {"data": backend.rows[:12] if cursor is None else backend.rows[12:],
                "nextCursor": "tail" if cursor is None else None}
    backend.threads = pages
    scan = QuotaDiscovery()
    scan.scan(store, backend, NOW)
    assert len(backend.reads) == 5
    scan.scan(store, backend, NOW+5)
    scan.scan(store, backend, NOW+10)
    scan.scan(store, backend, NOW+15)
    assert backend.pages == [None, "tail"] and len(backend.reads) == 13
    row = backend.rows[0]
    row["updatedAt"] += 1
    backend.turns[row["id"]]["status"] = "failed"
    scan.scan(store, backend, NOW+31)
    assert store.watched()[0]["id"] == row["id"]


def test_discovery_listing_failure_does_not_block_existing_watch(tmp_path):
    store, backend = Store(tmp_path), Backend()
    store.watch(backend.rows[0]["id"])
    store.set("enabled", True)
    backend.used = 10
    def broken(_=None):
        raise BackendError("fixture_failure")
    backend.threads = broken
    result = Engine(store, backend, lambda: NOW).tick()
    assert result["error"] == "thread_read_failed" and len(backend.sent) == 1


def test_legacy_cancelled_unwatched_sessions_remain_excluded(tmp_path):
    store, backend = Store(tmp_path), Backend()
    tid = backend.rows[0]["id"]
    with store.db() as db:
        db.execute("INSERT INTO recoveries(id,thread_id,turn_id,kind,state,due,created) VALUES (?,?,?,?,?,?,?)",
                   ("legacy", tid, backend.turns[tid]["id"], "usage_limit", "cancelled", NOW, NOW))
    restarted = Store(tmp_path)
    QuotaDiscovery().scan(restarted, backend, NOW)
    assert not restarted.watched()
    assert restarted.records()[0]["state"] == "cancelled"


def test_opencode_is_not_assumed_to_expose_codex_quota_errors(tmp_path):
    store, backend = Store(tmp_path, agent="opencode"), Backend()
    QuotaDiscovery().scan(store, backend, NOW)
    assert not backend.pages and not store.watched()
