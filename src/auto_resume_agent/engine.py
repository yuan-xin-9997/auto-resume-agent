import hashlib
import time

from .model import usage, category, delay, next_delay, numeric
from .store import engine_lock, valid_id
from .protocol import BackendError, is_compatibility_error
from .backends import snapshot
from . import window_keeper
from .discovery import QuotaDiscovery

MESSAGE = "Continue the unfinished work from this interruption. Respect all existing instructions and stop if user input or approval is required."


class Engine:
    def __init__(self, store, backend, clock=time.time):
        self.store, self.backend, self.clock = store, backend, clock
        self.snapshot = {"available": None, "windows": [], "reset_at": None}
        self.last_usage = 0
        self.discovery = QuotaDiscovery()

    def tick(self):
        with engine_lock(self.store.root) as owned:
            if not owned:
                return {"error": "another_monitor", "delay": 5, "usage": self.snapshot}
            return self._tick()

    def _tick(self):
        now = self.clock()
        enabled = self.store.get("enabled", False)
        records = self.store.records()
        due = min((r["due"] for r in records if r["state"] == "waiting"), default=None)
        keeper = window_keeper.status(self.store) if self.store.agent == "codex" else None
        keeper_due = keeper.get("next_at") if keeper and keeper["enabled"] else None
        # Re-query when a deadline arrives, including the first tick after system wake.
        if (now - self.last_usage >= 30 or (due is not None and due <= now)
                or (numeric(keeper_due) and now >= keeper_due+2 and self.last_usage < keeper_due+2)):
            try:
                self.snapshot = snapshot(self.backend)
            except BackendError as error:
                if is_compatibility_error(error):
                    return self._blocked(error)
                raise
            self.last_usage = now
            self.store.set("usage", {**self.snapshot, "checked_at": now})
        discovery_error = False
        try:
            self.discovery.scan(self.store, self.backend, now)
        except BackendError as error:
            if is_compatibility_error(error):
                return self._blocked(error)
            discovery_error = True
        except (KeyError, TypeError, ValueError):
            discovery_error = True
        watched = self.store.watched()
        problems = []
        for watch in watched:
            tid = watch["id"]
            try:
                metadata = self.backend.thread(tid)
                if not isinstance(metadata, dict):
                    raise ValueError("metadata")
                # Archived, imported, and subagent threads never receive automatic messages.
                source = metadata.get("source")
                if metadata.get("archived") or not isinstance(source, str) or source not in ("cli", "vscode", "appServer", "exec", "opencode"):
                    continue
                turn = self.backend.latest(tid)
                if not isinstance(turn, dict):
                    if turn is not None:
                        raise ValueError("turn")
                    continue
                if not getattr(self.backend, "valid_turn_id", valid_id)(turn.get("id")):
                    continue
                self._reconcile(tid, turn, records)
                kind = category(turn)
                completed = turn.get("completedAt")
                # Explicitly watching a session includes its latest retryable failure,
                # even when the user adds it more than a minute after the interruption.
                if not kind or not numeric(completed):
                    continue
                key = hashlib.sha256((str(watch["home"]) + tid + turn["id"]).encode()).hexdigest()[:32]
                current = next((r for r in records if r["id"] == key), None)
                if current is None:
                    # Bound chains of repeated failures; a new user turn resets the chain in a later version.
                    with self.store.db() as db:
                        recent = db.execute("SELECT count(*) FROM recoveries WHERE thread_id=? AND submitted>?",
                                            (tid, now-3600)).fetchone()[0]
                    initial = max(now, completed + delay(recent))
                    if numeric(turn.get("retryAt")):
                        initial = max(initial, turn["retryAt"])
                    if kind == "usage_limit" and self.snapshot.get("reset_at"):
                        initial = max(now, self.snapshot["reset_at"] + 2)
                    state = "waiting" if recent < 5 else "attention"
                    with self.store.db() as db:
                        db.execute("INSERT OR IGNORE INTO recoveries(id,thread_id,turn_id,kind,state,due,created) VALUES (?,?,?,?,?,?,?)",
                                   (key, tid, turn["id"], kind, state, initial, now))
                    self.store.event(tid, "detected" if state == "waiting" else "retry_budget")
                    current = {"id": key, "thread_id": tid, "turn_id": turn["id"], "kind": kind, "state": state, "due": initial}
                if enabled and current["state"] == "waiting" and current["due"] <= now:
                    self._attempt(current, now)
            except BackendError as error:
                if is_compatibility_error(error):
                    return self._blocked(error)
                problems.append(tid)
            except (KeyError, TypeError, ValueError):
                problems.append(tid)
        pending = [r["due"] for r in self.store.records() if r["state"] == "waiting" and r["due"] > self.clock()]
        if keeper is not None:
            keeper = window_keeper.tick(self.store, self.backend, self.snapshot, self.clock())
            if keeper["enabled"] and numeric(keeper.get("next_at")) and keeper["next_at"] > self.clock():
                pending.append(keeper["next_at"])
        return {"usage": self.snapshot, "enabled": enabled, "watched": len(watched),
                "window_keeper": keeper,
                "error": "thread_read_failed" if problems or discovery_error else None,
                "delay": next_delay(self.clock(), min(pending) if pending else None)}

    def _blocked(self, error):
        # An adapter contract change is not a per-session hiccup: do not send
        # anything until doctor/the adapter is updated.
        return {"usage": self.snapshot, "enabled": self.store.get("enabled", False),
                "watched": len(self.store.watched()),
                "window_keeper": window_keeper.status(self.store) if self.store.agent == "codex" else None,
                "error": str(error), "delay": 10}

    def _reconcile(self, tid, turn, records):
        for row in records:
            if row["thread_id"] != tid:
                continue
            if row["state"] == "waiting" and row["turn_id"] != turn["id"]:
                self.store.update(row["id"], "superseded")
            elif row["state"] == "waiting" and turn.get("status") in ("completed", "interrupted"):
                self.store.update(row["id"], "superseded")
            elif row["state"] in ("sending", "queued", "accepted", "uncertain"):
                if turn["id"] != row["turn_id"] and turn.get("status") != "interrupted":
                    # Metadata proves progression, but not who sent the new user message.
                    self.store.update(row["id"], "progressed")
                    self.store.event(tid, "progressed")
                elif row["state"] == "sending":
                    self.store.update(row["id"], "uncertain", "delivery_unknown")

    def _attempt(self, row, now):
        available = self.snapshot.get("available")
        if available is not True and getattr(self.backend, "quota_required", True):
            reset = self.snapshot.get("reset_at")
            due = reset + 2 if reset and reset > now else now + 30
            self.store.update(row["id"], "waiting", "waiting_reset" if reset else "quota_unknown", due)
            return
        latest = self.backend.latest(row["thread_id"])
        if latest is not None and not isinstance(latest, dict):
            raise ValueError("latest_turn")
        if not latest or latest.get("id") != row["turn_id"] or category(latest) != row["kind"]:
            self.store.update(row["id"], "superseded")
            return
        # Commit intent before crossing the process boundary. Crashes are never blindly retried.
        with self.store.db() as db:
            # Pause/unwatch in another UI between check and claim must take effect.
            enabled = db.execute("SELECT value FROM settings WHERE key='enabled'").fetchone()
            watched = db.execute("SELECT 1 FROM watched WHERE id=? AND home=?",
                                 (row["thread_id"], self.store.source)).fetchone()
            if not watched or not enabled or enabled[0] != "true":
                return
            changed = db.execute("UPDATE recoveries SET state='sending',submitted=? WHERE id=? AND state='waiting'",
                                 (now, row["id"])).rowcount
        if not changed:
            return
        # Pause, unwatch, or an explicit cancel after the claim still wins. The
        # final process boundary is not atomic, but this closes the claim race.
        with self.store.db() as db:
            enabled = db.execute("SELECT value FROM settings WHERE key='enabled'").fetchone()
            watched = db.execute("SELECT 1 FROM watched WHERE id=? AND home=?",
                                 (row["thread_id"], self.store.source)).fetchone()
            state = db.execute("SELECT state FROM recoveries WHERE id=?", (row["id"],)).fetchone()
        if not watched or not enabled or enabled[0] != "true" or not state or state[0] != "sending":
            if state and state[0] == "sending":
                self.store.update(row["id"], "cancelled", "cancelled_before_submit")
            return
        result = self.backend.submit(row["thread_id"], MESSAGE + "\n[Auto Resume Agent: " + row["id"] + "]")
        if result not in ("queued", "accepted", "uncertain"):
            result = "uncertain"
        self.store.update(row["id"], result, "open_session" if result == "queued" else "" if result == "accepted" else "delivery_unknown")
        self.store.event(row["thread_id"], result)
