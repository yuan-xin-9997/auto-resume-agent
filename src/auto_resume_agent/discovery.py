"""Bounded discovery of running or quota-exhausted Codex/OpenCode sessions."""
import time

from .model import category, numeric
from .protocol import BackendError, is_compatibility_error
from .store import valid_id


class QuotaDiscovery:
    def __init__(self):
        self.pending = []
        self.cursor = None
        self.head_at = 0
        self.seen = {}
        self.running = set()

    def scan(self, store, backend, now):
        if not callable(getattr(backend, "threads", None)):
            return
        if store.agent == "opencode":
            from .opencode import valid_session
            valid = valid_session
            sources = ("opencode",)
            shape_error = "opencode_response_incompatible"
        else:
            if not store.get("auto_watch_quota", True):
                return
            valid = valid_id
            sources = ("cli", "vscode", "appServer", "exec")
            shape_error = "codex_response_incompatible"
        begin = time.monotonic()
        head = now >= self.head_at
        page_data = []
        if head or (not self.pending and self.cursor):
            page = backend.threads(None if head else self.cursor)
            if not isinstance(page, dict) or not isinstance(page.get("data", []), list):
                raise BackendError(shape_error)
            if any(not isinstance(row, dict) for row in page.get("data", [])):
                raise BackendError(shape_error)
            store.remember_sessions(page.get("data", []))
            page_data = page.get("data", [])
            if not head or self.cursor is None:
                self.cursor = page.get("nextCursor")
            if head:
                self.head_at = now + store.interval()
        watched = {r["id"] for r in store.watched()}
        with store.db() as db:
            excluded = {r[0] for r in db.execute("SELECT id FROM watch_exclusions WHERE home=?", (store.source,))}
            helpers = {r[0] for r in db.execute("SELECT thread_id FROM window_starts WHERE home=?", (store.source,))}
        running = set()
        if store.agent == "opencode" and callable(getattr(backend, "running", None)):
            try:
                running = backend.running()
            except BackendError as error:
                if is_compatibility_error(error):
                    raise
                running = set()
        self.running = running
        # Running sessions are adopted from the active set, not only from
        # updatedAt. A completed session can start a new turn without its
        # cached updatedAt changing before the next scan.
        for row in page_data:
            tid = row.get("id")
            if not valid(tid) or tid in watched or tid in excluded or tid in helpers:
                continue
            if (row.get("archived") or row.get("source") not in sources
                    or row.get("name") == "Auto Resume Agent · 5h window"):
                continue
            if tid in running:
                if store.get("auto_watch_quota", True) and store.watch(tid, automatic=True):
                    store.event(tid, "auto_running")
                    watched.add(tid)
                self.seen[tid] = row.get("updatedAt")
        # The active endpoint is global. Adopt running sessions from other
        # workspaces even when the configured session-list page is scoped to
        # one directory.
        page_ids = {row.get("id") for row in page_data if isinstance(row, dict)}
        for sid in running:
            if (not valid(sid) or sid in page_ids or sid in watched
                    or sid in excluded or sid in helpers):
                continue
            try:
                metadata = backend.thread(sid)
            except BackendError as error:
                if is_compatibility_error(error):
                    raise
                continue
            if (not isinstance(metadata, dict) or metadata.get("archived")
                    or metadata.get("source") not in sources):
                continue
            if store.get("auto_watch_quota", True) and store.watch(sid, automatic=True):
                store.event(sid, "auto_running")
                watched.add(sid)
            self.seen[sid] = None
        rows = [r for r in page_data if valid(r.get("id")) and r["id"] not in watched
                and (r.get("updatedAt") is None or self.seen.get(r["id"]) != r.get("updatedAt"))]
        fresh = {r["id"]: r for r in rows}
        self.pending = list(fresh.values()) + [r for r in self.pending if r["id"] not in fresh]
        if store.agent != "opencode" and page_data:
            # Rotate a few recent unchanged rows through latest() so a
            # completed-to-running transition is not hidden by the cache.
            known = {r["id"] for r in self.pending}
            stale = [r for r in page_data if valid(r.get("id"))
                     and r["id"] not in watched and r["id"] not in excluded and r["id"] not in helpers
                     and r["id"] not in known and not r.get("archived")
                     and r.get("source") in sources]
            self.pending.extend(stale[:5])
        # Keep discovery bounded so large histories cannot monopolize the monitor.
        valid_turn = getattr(backend, "valid_turn_id", valid_id)
        for _ in range(min(5, len(self.pending))):
            if time.monotonic() - begin >= 2:
                break
            row = self.pending.pop(0)
            tid = row["id"]
            if tid in watched or tid in excluded or tid in helpers:
                self.seen[tid] = row.get("updatedAt")
                continue
            if (row.get("archived") or row.get("source") not in sources
                    or row.get("name") == "Auto Resume Agent · 5h window"):
                self.seen[tid] = row.get("updatedAt")
                continue
            if tid in running:
                if store.get("auto_watch_quota", True) and store.watch(tid, automatic=True):
                    store.event(tid, "auto_running")
                    watched.add(tid)
                self.seen[tid] = row.get("updatedAt")
                continue
            try:
                turn = backend.latest(tid)
                if (isinstance(turn, dict) and valid_turn(turn.get("id"))
                        and (turn.get("status") == "inProgress" or
                             (category(turn) == "usage_limit" and numeric(turn.get("completedAt"))))
                        and store.get("auto_watch_quota", True)):
                    if store.watch(tid, automatic=True):
                        store.event(tid, "auto_running" if turn.get("status") == "inProgress" else "auto_watched")
                self.seen[tid] = row.get("updatedAt")
            except BackendError as error:
                if is_compatibility_error(error):
                    raise
                continue
            except (KeyError, TypeError, ValueError):
                continue
