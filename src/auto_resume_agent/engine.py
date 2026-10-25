import hashlib
import time

from .model import usage, category, delay, next_delay, numeric
from .store import engine_lock, valid_id
from .protocol import BackendError

MESSAGE = "Continue the unfinished work from this interruption. Respect all existing instructions and stop if user input or approval is required."


class Engine:
    def __init__(self, store, backend, clock=time.time):
        self.store, self.backend, self.clock = store, backend, clock
        self.snapshot = {"available": None, "windows": [], "reset_at": None}
        self.last_usage = 0

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
        # Re-query when a deadline arrives, including the first tick after system wake.
        if now - self.last_usage >= 30 or (due is not None and due <= now):
            self.snapshot = usage(self.backend.usage())
            self.last_usage = now
            self.store.set("usage", {**self.snapshot, "checked_at": now})
        watched = self.store.watched()
        problems = []
        for watch in watched:
            tid = watch["id"]
            try:
                metadata = self.backend.thread(tid)
                # Archived, imported, and subagent threads never receive automatic messages.
                source = metadata.get("source")
                if metadata.get("archived") or not isinstance(source, str) or source not in ("cli", "vscode", "appServer", "exec"):
                    continue
                turn = self.backend.latest(tid)
                if not turn or not valid_id(turn.get("id")):
                    continue
                self._reconcile(tid, turn, records)
                kind = category(turn)
                completed = turn.get("completedAt")
                if not kind or not numeric(completed) or completed < watch["armed"]:
                    continue
                key = hashlib.sha256((str(watch["home"]) + tid + turn["id"]).encode()).hexdigest()[:32]
                current = next((r for r in records if r["id"] == key), None)
                if current is None:
                    # Bound chains of repeated failures; a new user turn resets the chain in a later version.
                    recent = sum(r["thread_id"] == tid and r["submitted"] is not None and now-r["submitted"] < 3600 for r in records)
                    initial = max(now, completed + delay(recent))
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
            except (BackendError, KeyError, TypeError, ValueError):
                problems.append(tid)
        pending = [r["due"] for r in self.store.records() if r["state"] == "waiting"]
        return {"usage": self.snapshot, "enabled": enabled, "watched": len(watched),
                "error": "thread_read_failed" if problems else None,
                "delay": next_delay(self.clock(), min(pending) if pending else None)}

    def _reconcile(self, tid, turn, records):
        for row in records:
            if row["thread_id"] != tid:
                continue
            if row["state"] == "waiting" and row["turn_id"] != turn["id"]:
                self.store.update(row["id"], "superseded")
            elif row["state"] in ("sending", "queued", "uncertain"):
                if turn["id"] != row["turn_id"]:
                    # Metadata proves progression, but not who sent the new user message.
                    self.store.update(row["id"], "progressed")
                    self.store.event(tid, "progressed")
                elif row["state"] == "sending":
                    self.store.update(row["id"], "uncertain", "delivery_unknown")

    def _attempt(self, row, now):
        available = self.snapshot.get("available")
        if available is not True:
            reset = self.snapshot.get("reset_at")
            due = reset + 2 if reset and reset > now else now + 30
            self.store.update(row["id"], "waiting", "waiting_reset" if reset else "quota_unknown", due)
            return
        latest = self.backend.latest(row["thread_id"])
        if not latest or latest.get("id") != row["turn_id"] or category(latest) != row["kind"]:
            self.store.update(row["id"], "superseded")
            return
        # Commit intent before crossing the process boundary. Crashes are never blindly retried.
        with self.store.db() as db:
            # Pause/unwatch in another UI between check and claim must take effect.
            enabled = db.execute("SELECT value FROM settings WHERE key='enabled'").fetchone()
            watched = db.execute("SELECT 1 FROM watched WHERE id=?", (row["thread_id"],)).fetchone()
            if not watched or not enabled or enabled[0] != "true":
                return
            changed = db.execute("UPDATE recoveries SET state='sending',submitted=? WHERE id=? AND state='waiting'",
                                 (now, row["id"])).rowcount
        if not changed:
            return
        result = self.backend.submit(row["thread_id"], MESSAGE + "\n[Auto Resume Agent: " + row["id"] + "]")
        self.store.update(row["id"], result, "open_session" if result == "queued" else "delivery_unknown")
        self.store.event(row["thread_id"], result)
