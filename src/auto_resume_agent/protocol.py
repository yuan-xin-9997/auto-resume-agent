"""Bounded, read-only app-server client. Authentication stays in Codex."""
import json
import os
import queue
import shutil
import subprocess
import threading
import time
import sys
import contextlib
from pathlib import Path

from . import __version__
from .paths import codex_home

NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
SPAWN_LOCK = threading.Lock()


def external_environment():
    env = os.environ.copy()
    bundle = getattr(sys, "_MEIPASS", None)
    if not bundle:
        return env
    def outside(entry):
        try:
            return not Path(entry).resolve().is_relative_to(Path(bundle).resolve())
        except (ValueError, OSError):
            return True
    for key in ("PATH", "DYLD_LIBRARY_PATH"):
        if key in env:
            env[key] = os.pathsep.join(p for p in env[key].split(os.pathsep) if p and outside(p))
    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env["LD_LIBRARY_PATH_ORIG"]
    else:
        env.pop("LD_LIBRARY_PATH", None)
    return env


@contextlib.contextmanager
def external_spawn():
    # PyInstaller's DLL directory is inherited by external Node/Codex processes.
    with SPAWN_LOCK:
        if os.name == "nt" and getattr(sys, "frozen", False):
            import ctypes
            library = ctypes.windll.kernel32
            previous = ctypes.create_unicode_buffer(32768)
            library.GetDllDirectoryW(len(previous), previous)
            library.SetDllDirectoryW(None)
            try:
                yield
            finally:
                library.SetDllDirectoryW(previous.value or None)
        else:
            yield


class BackendError(RuntimeError):
    pass


def command(executable=None):
    found = executable or shutil.which("codex")
    if not found:
        # GUI processes on macOS do not inherit the interactive shell's PATH.
        found = next((str(p) for p in [Path("/opt/homebrew/bin/codex"),
                     Path("/usr/local/bin/codex"), Path.home() / ".local/bin/codex"] if p.is_file()), None)
    if not found:
        raise BackendError("codex_missing")
    path = Path(found).expanduser().resolve()
    if path.suffix.lower() in (".cmd", ".bat", ".ps1"):
        script = path.parent / "node_modules/@openai/codex/bin/codex.js"
        node = shutil.which("node")
        if node and script.is_file():
            return [node, str(script)]
        raise BackendError("codex_wrapper_unsupported")
    if not path.is_file():
        raise BackendError("codex_missing")
    return [str(path)]


class Codex:
    METHODS = {"initialize", "account/rateLimits/read", "thread/list", "thread/read", "thread/turns/list"}

    def __init__(self, executable=None, timeout=20):
        self.argv = command(executable)
        self.timeout = timeout
        self.process = None
        self.sequence = 0
        self.responses = queue.Queue(maxsize=64)

    def start(self):
        if self.process and self.process.poll() is None:
            return
        self.close()
        self.responses = queue.Queue(maxsize=64)
        codex_home().mkdir(parents=True, exist_ok=True)
        with external_spawn():
            self.process = subprocess.Popen(
                self.argv + ["app-server", "--stdio"], stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                encoding="utf-8", bufsize=1, creationflags=NO_WINDOW,
                cwd=codex_home(), shell=False, env=external_environment())
        self.reader = threading.Thread(target=self._read, args=(self.process, self.responses), daemon=True)
        self.reader.start()
        try:
            result = self.call("initialize", {"clientInfo": {"name": "auto_resume_agent", "version": __version__},
                               "capabilities": {"experimentalApi": True}}, initialize=True)
            if result.get("codexHome") and Path(result["codexHome"]).resolve() != codex_home():
                raise BackendError("codex_home_mismatch")
            self._write({"method": "initialized"})
        except BaseException:
            self.close()
            raise

    def _read(self, process, responses):
        try:
            for line in process.stdout:
                if len(line) > 8 * 1024 * 1024:
                    break
                try:
                    value = json.loads(line)
                except ValueError:
                    continue
                if isinstance(value, dict) and "id" in value:
                    if "method" in value:
                        # This client cannot approve tools, run commands, or start turns.
                        process.stdin.write(json.dumps({"id": value["id"], "error": {
                            "code": -32601, "message": "Read-only client"}}) + "\n")
                        process.stdin.flush()
                    else:
                        responses.put_nowait(value)
        except (OSError, ValueError, queue.Full):
            pass
        finally:
            try:
                responses.put_nowait({"disconnected": True})
            except queue.Full:
                pass

    def _write(self, value):
        self.process.stdin.write(json.dumps(value) + "\n")
        self.process.stdin.flush()

    def call(self, method, params=None, initialize=False):
        if method not in self.METHODS:
            raise BackendError("method_not_allowed")
        if not initialize:
            self.start()
        self.sequence += 1
        request_id = self.sequence
        try:
            self._write({"id": request_id, "method": method, "params": params or {}})
            end = time.monotonic() + self.timeout
            while time.monotonic() < end:
                result = self.responses.get(timeout=max(0.01, end - time.monotonic()))
                if result.get("disconnected"):
                    raise BackendError("codex_disconnected")
                if result.get("id") != request_id:
                    continue
                if "error" in result:
                    # Do not persist raw errors, account details, or conversation text.
                    raise BackendError("protocol_error_" + str(result["error"].get("code", "unknown")))
                return result.get("result", {})
        except (OSError, ValueError, queue.Empty):
            self.close()
            raise BackendError("codex_timeout_or_disconnected") from None
        raise BackendError("codex_timeout_or_disconnected")

    def usage(self):
        return self.call("account/rateLimits/read")

    def threads(self, cursor=None):
        return self.call("thread/list", {"limit": 100, "cursor": cursor, "sortKey": "updated_at",
                         "sourceKinds": ["cli", "vscode", "appServer", "exec"], "archived": False})

    def thread(self, thread_id):
        return self.call("thread/read", {"threadId": thread_id, "includeTurns": False})["thread"]

    def latest(self, thread_id):
        rows = self.call("thread/turns/list", {"threadId": thread_id, "limit": 1,
                         "sortDirection": "desc", "itemsView": "notLoaded"}).get("data", [])
        return rows[0] if rows else None

    def submit(self, thread_id, message):
        process = None
        try:
            with external_spawn():
                process = subprocess.Popen(self.argv + ["queue", "--thread", thread_id, "--message", message],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                    encoding="utf-8", errors="replace", env=external_environment(),
                                    creationflags=NO_WINDOW, cwd=codex_home(), shell=False)
            process.communicate(timeout=25)
        except (subprocess.TimeoutExpired, OSError):
            if process and process.poll() is None:
                process.kill()
                process.communicate()
            return "uncertain"
        # A nonzero exit can happen after the server accepted the message. Never resend blindly.
        return "queued" if process.returncode == 0 else "uncertain"

    def close(self):
        process, self.process = self.process, None
        if not process:
            return
        try:
            if process.stdin:
                process.stdin.close()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            process.kill()
            process.wait(timeout=2)
        if hasattr(self, "reader"):
            self.reader.join(timeout=1)
        if process.stdout:
            process.stdout.close()
