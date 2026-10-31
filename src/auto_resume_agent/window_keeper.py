"""Opt-in, at-most-once first request after a reported Codex five-hour window."""
from .model import numeric

HOURS = 5 * 60 * 60


def key(store, name):
    return "window_keeper_" + name + ":" + store.source


def enabled(store):
    return store.agent == "codex" and store.get(key(store, "enabled"), False) is True


def set_enabled(store, value):
    if store.agent != "codex":
        raise ValueError("codex_only")
    store.set(key(store, "enabled"), bool(value))


def status(store):
    with store.db() as db:
        row = db.execute("SELECT reset_at,state,thread_id,created FROM window_starts WHERE home=? ORDER BY created DESC LIMIT 1",
                         (store.source,)).fetchone()
    return {"enabled": enabled(store), "next_at": store.get(key(store, "due")),
            "last_attempt": dict(row) if row else None}


def reset_at(snapshot):
    windows = [w for w in snapshot.get("windows", []) if w.get("bucket") == "codex"
               and w.get("window") == "primary" and w.get("minutes") == 300]
    if len(windows) != 1:
        return None
    value = windows[0].get("reset_at")
    return value if numeric(value) and 946684800 <= value <= 4102444800 else None


def tick(store, backend, snapshot, now, has_pending=False):
    state = status(store)
    if not state["enabled"]:
        return state
    observed = reset_at(snapshot)
    if observed is None:
        return {**state, "reason": "keeper_no_window"}
    primary = next(w for w in snapshot["windows"] if w.get("bucket") == "codex"
                   and w.get("window") == "primary" and w.get("minutes") == 300)
    if numeric(primary.get("used_percent")) and primary["used_percent"] >= 100:
        store.set(key(store, "exhausted"), observed)
    due = state["next_at"]
    # A future server deadline proves a window is already active. Follow it
    # instead of creating a helper for an expired deadline.
    if not numeric(due) or (observed > now and observed != due):
        due = observed
        store.set(key(store, "due"), due)
    state["next_at"] = due + 2
    if now < due + 2:
        return {**state, "reason": "keeper_waiting"}
    if has_pending:
        return {**state, "reason": "keeper_recovery_first"}
    if store.get(key(store, "exhausted")) != due:
        return {**state, "reason": "keeper_not_exhausted"}
    with store.db() as db:
        attempt = db.execute("SELECT state FROM window_starts WHERE home=? AND reset_at=?", (store.source, due)).fetchone()
    if attempt:
        if attempt["state"] == "sending":
            with store.db() as db:
                db.execute("UPDATE window_starts SET state='uncertain' WHERE home=? AND reset_at=?", (store.source, due))
        if observed > due and observed > now:
            store.set(key(store, "due"), observed)
            return {**status(store), "reason": "keeper_waiting"}
        return {**status(store), "reason": "keeper_waiting_update"}
    last = state["last_attempt"]
    if last and now < last["created"] + HOURS:
        return {**state, "next_at": last["created"] + HOURS, "reason": "keeper_waiting"}
    if snapshot.get("available") is not True:
        return {**state, "reason": "keeper_waiting_quota"}
    with store.db() as db:
        flag = db.execute("SELECT value FROM settings WHERE key=?", (key(store, "enabled"),)).fetchone()
        if not flag or flag[0] != "true":
            return status(store)
        claimed = db.execute("INSERT OR IGNORE INTO window_starts(home,reset_at,state,created) VALUES (?,?,'sending',?)",
                             (store.source, due, now)).rowcount
    if not claimed:
        return status(store)

    def created(thread_id):
        with store.db() as db:
            db.execute("UPDATE window_starts SET thread_id=? WHERE home=? AND reset_at=?", (thread_id, store.source, due))

    # Intent is already durable: an exception or crash must never resend this window.
    outcome = "uncertain"
    try:
        outcome = backend.activate_window(created, lambda: enabled(store))
        if outcome not in ("completed", "accepted", "cancelled", "failed", "uncertain"):
            outcome = "uncertain"
    finally:
        with store.db() as db:
            db.execute("UPDATE window_starts SET state=? WHERE home=? AND reset_at=?", (outcome, store.source, due))
        store.event(None, "keeper_" + outcome)
    return {**status(store), "reason": "keeper_waiting_update"}
