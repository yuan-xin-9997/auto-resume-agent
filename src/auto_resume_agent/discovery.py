"""Bounded discovery of Codex sessions whose latest turn exhausted quota."""
import time

from .model import category, numeric
from .protocol import BackendError
from .store import valid_id


class QuotaDiscovery:
    def __init__(self):
        self.pending = []
        self.cursor = None
        self.head_at = 0
        self.seen = {}

    def scan(self, store, backend, now):
        if (store.agent != "codex" or not store.get("auto_watch_quota", True)
                or not callable(getattr(backend, "threads", None))):
            return
        begin = time.monotonic()
        head = now >= self.head_at
        if head or (not self.pending and self.cursor):
            page = backend.threads(None if head else self.cursor)
            rows = [r for r in page.get("data", []) if valid_id(r.get("id"))
                    and (r.get("updatedAt") is None or self.seen.get(r["id"]) != r["updatedAt"])]
            fresh = {r["id"]: r for r in rows}
            self.pending = list(fresh.values()) + [r for r in self.pending if r["id"] not in fresh]
            if not head or self.cursor is None:
                self.cursor = page.get("nextCursor")
            if head:
                self.head_at = now + 30
        watched = {r["id"] for r in store.watched()}
        with store.db() as db:
            excluded = {r[0] for r in db.execute("SELECT id FROM watch_exclusions WHERE home=?", (store.source,))}
            helpers = {r[0] for r in db.execute("SELECT thread_id FROM window_starts WHERE home=?", (store.source,))}
        # Keep discovery bounded so large histories cannot monopolize the monitor.
        for _ in range(min(5, len(self.pending))):
            if time.monotonic() - begin >= 2:
                break
            row = self.pending.pop(0)
            tid = row["id"]
            if tid in watched or tid in excluded or tid in helpers:
                self.seen[tid] = row.get("updatedAt")
                continue
            if (row.get("archived") or row.get("source") not in ("cli", "vscode", "appServer", "exec")
                    or row.get("name") == "Auto Resume Agent · 5h window"):
                self.seen[tid] = row.get("updatedAt")
                continue
            try:
                turn = backend.latest(tid)
                if (category(turn) == "usage_limit" and valid_id(turn.get("id"))
                        and numeric(turn.get("completedAt")) and store.get("auto_watch_quota", True)):
                    if store.watch(tid, automatic=True):
                        store.event(tid, "auto_watched")
                self.seen[tid] = row.get("updatedAt")
            except (BackendError, KeyError, TypeError, ValueError):
                continue
