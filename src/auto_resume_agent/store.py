import contextlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path

from .paths import data_dir, codex_home


def valid_id(value):
    try:
        return str(uuid.UUID(value)) == value.lower()
    except (ValueError, TypeError, AttributeError):
        return False


class Store:
    def __init__(self, root=None, agent="codex", source=None):
        self.agent = agent
        self.source = source or str(codex_home())
        self.root = Path(root) if root else data_dir()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.root / "state.sqlite3"
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS watched (id TEXT PRIMARY KEY,armed REAL NOT NULL, home TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS watch_exclusions (id TEXT NOT NULL,home TEXT NOT NULL,PRIMARY KEY(id,home));
                CREATE TABLE IF NOT EXISTS recoveries (
                    id TEXT PRIMARY KEY,thread_id TEXT NOT NULL,turn_id TEXT NOT NULL,
                    kind TEXT NOT NULL,state TEXT NOT NULL,due REAL NOT NULL,
                    created REAL NOT NULL,submitted REAL,detail TEXT NOT NULL DEFAULT '');
                CREATE TABLE IF NOT EXISTS session_names (
                    home TEXT NOT NULL,id TEXT NOT NULL,name TEXT NOT NULL,PRIMARY KEY(home,id));
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,time REAL NOT NULL,thread_id TEXT,code TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS window_starts (
                    home TEXT NOT NULL, reset_at REAL NOT NULL, state TEXT NOT NULL,
                    thread_id TEXT, created REAL NOT NULL, PRIMARY KEY(home,reset_at));
            ''')
            if self.agent == "codex":
                db.execute("INSERT OR IGNORE INTO settings VALUES ('enabled','true')")
            # Preserve legacy manual cancellations when default discovery is introduced.
            db.execute("INSERT OR IGNORE INTO watch_exclusions SELECT DISTINCT thread_id,? FROM recoveries "
                       "WHERE state='cancelled' AND thread_id NOT IN (SELECT id FROM watched)", (self.source,))
            # A claim that survived a crash may already have been delivered.
            # Reconciliation changes its label, never submits a second message.
        if os.name != "nt":
            self.path.chmod(0o600)

    @contextlib.contextmanager
    def db(self):
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def interval(self):
        value = self.get("codex_interval" if self.agent == "codex" else "poll_interval", 30)
        return value if type(value) is int and 5 <= value <= 3600 else 30

    def get(self, key, default=None):
        with self.db() as db:
            row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key, value):
        with self.db() as db:
            db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value)))

    def watch(self, thread_id, automatic=False):
        from .opencode import valid_session
        if not (valid_session(thread_id) if self.agent == "opencode" else valid_id(thread_id)):
            raise ValueError("invalid_thread_id")
        with self.db() as db:
            flag = db.execute("SELECT value FROM settings WHERE key='auto_watch_quota'").fetchone() if automatic else None
            if automatic and flag and flag[0] != "true":
                return False
            if automatic and db.execute("SELECT 1 FROM watch_exclusions WHERE id=? AND home=?", (thread_id, self.source)).fetchone():
                return False
            changed = db.execute("INSERT OR IGNORE INTO watched VALUES (?,?,?)", (thread_id, time.time() - 60, self.source)).rowcount
            if not automatic:
                db.execute("DELETE FROM watch_exclusions WHERE id=? AND home=?", (thread_id, self.source))
            return bool(changed)

    def unwatch(self, thread_id):
        with self.db() as db:
            db.execute("INSERT OR IGNORE INTO watch_exclusions VALUES (?,?)", (thread_id, self.source))
            db.execute("DELETE FROM watched WHERE id=? AND home=?", (thread_id, self.source))
            # A claimed-but-not-yet-submitted record is still user-cancellable.
            db.execute("UPDATE recoveries SET state='cancelled' WHERE thread_id=? AND state IN ('waiting','sending')",
                       (thread_id,))

    def cancel(self, record_id):
        with self.db() as db:
            return bool(db.execute(
                "UPDATE recoveries SET state='cancelled' WHERE id=? AND state IN ('waiting','sending')",
                (record_id,)).rowcount)

    def watched(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM watched WHERE home=?", (self.source,))]

    def records(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM recoveries ORDER BY created DESC LIMIT 500")]

    def event(self, thread_id, code):
        with self.db() as db:
            db.execute("INSERT INTO events(time,thread_id,code) VALUES (?,?,?)", (time.time(), thread_id, code))
            db.execute("DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT 1000)")

    def remember_sessions(self, rows):
        values = [(self.source, row["id"], row["name"]) for row in rows
                  if row.get("id") and isinstance(row.get("name"), str) and row["name"].strip()]
        if values:
            with self.db() as db:
                db.executemany("INSERT INTO session_names VALUES (?,?,?) ON CONFLICT(home,id) DO UPDATE SET name=excluded.name WHERE name!=excluded.name", values)

    def session_names(self):
        with self.db() as db:
            return {r["id"]: r["name"] for r in db.execute("SELECT id,name FROM session_names WHERE home=?", (self.source,))}

    def events(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100")]

    def update(self, record_id, state, detail="", due=None):
        with self.db() as db:
            if due is None:
                db.execute("UPDATE recoveries SET state=?,detail=? WHERE id=?", (state, detail, record_id))
            else:
                db.execute("UPDATE recoveries SET state=?,detail=?,due=? WHERE id=?", (state, detail, due, record_id))


@contextlib.contextmanager
def engine_lock(root):
    """OS releases the lock after a crash; every sender uses this same lock."""
    path = Path(root) / "monitor.lock"
    with path.open("a+b") as handle:
        if path.stat().st_size == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        try:
            yield True
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
