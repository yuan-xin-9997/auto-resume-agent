"""Read-only monitor client; the opt-in helper uses a separate, owned-thread client."""
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
from urllib.parse import urlsplit

from . import __version__
from .paths import codex_home
from .store import valid_id

NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
SPAWN_LOCK = threading.Lock()
COMPATIBILITY_PREFIXES = (
    "codex_experimental_api_missing",
    "codex_protocol_incompatible",
    "codex_response_incompatible",
    "opencode_experimental_api_missing",
    "opencode_response_incompatible",
    "opencode_invalid_response",
    "opencode_unexpected_cursor",
)


def proxy_url(value):
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or not parsed.port):
            raise ValueError()
    except ValueError:
        raise BackendError("codex_invalid_proxy") from None
    return value


def external_environment(proxy=None):
    env = os.environ.copy()
    if proxy:
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            env[key] = proxy
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


def compatibility_code(value):
    text = str(value)
    return next((prefix for prefix in COMPATIBILITY_PREFIXES
                 if text == prefix or text.startswith(prefix + ":")), None)


def is_compatibility_error(error):
    return isinstance(error, BackendError) and compatibility_code(error) is not None


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

    def __init__(self, executable=None, timeout=20, proxy=None):
        self.argv = command(executable)
        self.proxy = proxy_url(proxy)
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
        debug_log = open(os.environ["ARA_DEBUG_LOG"], "ab") if os.environ.get("ARA_DEBUG_LOG") else None
        try:
            with external_spawn():
                self.process = subprocess.Popen(
                    self.argv + ["app-server", "--stdio"], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=debug_log or subprocess.DEVNULL, text=True,
                    encoding="utf-8", bufsize=1, creationflags=NO_WINDOW,
                    cwd=codex_home(), shell=False, env=external_environment(self.proxy))
        finally:
            if debug_log:
                debug_log.close()
        self.reader = threading.Thread(target=self._read, args=(self.process, self.responses), daemon=True)
        self.reader.start()
        try:
            result = self.call("initialize", {"clientInfo": {"name": "auto_resume_agent", "version": __version__},
                               "capabilities": {"experimentalApi": True}}, initialize=True)
            if not isinstance(result, dict):
                raise BackendError("codex_response_incompatible")
            home = result.get("codexHome")
            if home is not None and not isinstance(home, str):
                raise BackendError("codex_response_incompatible")
            if home and Path(home).resolve() != codex_home():
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
                elif isinstance(value, dict) and "method" in value:
                    self.notification(value)
        except (OSError, ValueError, queue.Full) as error:
            if os.environ.get("ARA_DEBUG_LOG"):
                with open(os.environ["ARA_DEBUG_LOG"], "a", encoding="utf-8") as log:
                    log.write("reader: " + type(error).__name__ + " errno=" + str(getattr(error, "errno", None)) + "\n")
        finally:
            try:
                responses.put_nowait({"disconnected": True})
            except queue.Full:
                pass

    def _write(self, value):
        self.process.stdin.write(json.dumps(value) + "\n")
        self.process.stdin.flush()

    def notification(self, value):
        pass

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
                    try:
                        status = self.process.wait(timeout=0.2)
                    except subprocess.TimeoutExpired:
                        status = "running"
                    raise BackendError("codex_disconnected_" + str(status))
                if result.get("id") != request_id:
                    continue
                if "error" in result:
                    # Do not persist raw errors, account details, or conversation text.
                    error = result["error"]
                    code = error.get("code") if isinstance(error, dict) else None
                    if code == -32601:
                        raise BackendError("codex_experimental_api_missing")
                    if code in (-32600, -32602, -32700):
                        raise BackendError("codex_protocol_incompatible")
                    raise BackendError("protocol_error_" + str(code if code is not None else "unknown"))
                return result.get("result", {})
        except (OSError, ValueError, queue.Empty):
            self.close()
            raise BackendError("codex_timeout_or_disconnected") from None
        raise BackendError("codex_timeout_or_disconnected")

    def usage(self):
        value = self.call("account/rateLimits/read")
        if (not isinstance(value, dict) or not any(key in value for key in (
                "rateLimits", "rateLimitsByLimitId", "ordinaryUsageAllowed"))):
            raise BackendError("codex_response_incompatible")
        return value

    def activate_window(self, on_created, can_send):
        from .window_request import send
        return send(self, on_created, can_send)

    def threads(self, cursor=None):
        value = self.call("thread/list", {"limit": 100, "cursor": cursor, "sortKey": "updated_at",
                         "sourceKinds": ["cli", "vscode", "appServer", "exec"], "archived": False})
        if not isinstance(value, dict) or not isinstance(value.get("data", []), list):
            raise BackendError("codex_response_incompatible")
        if any(not isinstance(row, dict) or not valid_id(row.get("id")) for row in value.get("data", [])):
            raise BackendError("codex_response_incompatible")
        if value.get("nextCursor") is not None and not isinstance(value["nextCursor"], str):
            raise BackendError("codex_response_incompatible")
        return value

    def thread(self, thread_id):
        value = self.call("thread/read", {"threadId": thread_id, "includeTurns": False})
        thread = value.get("thread") if isinstance(value, dict) else None
        if not isinstance(thread, dict) or thread.get("id") != thread_id:
            raise BackendError("codex_response_incompatible")
        return thread

    def latest(self, thread_id):
        value = self.call("thread/turns/list", {"threadId": thread_id, "limit": 1,
                         "sortDirection": "desc", "itemsView": "notLoaded"})
        rows = value.get("data") if isinstance(value, dict) else None
        if not isinstance(rows, list):
            raise BackendError("codex_response_incompatible")
        if not rows:
            return None
        if not isinstance(rows[0], dict) or not valid_id(rows[0].get("id")):
            raise BackendError("codex_response_incompatible")
        return rows[0]

    def submit(self, thread_id, message):
        if not valid_id(thread_id):
            return "uncertain"
        process = None
        try:
            with external_spawn():
                process = subprocess.Popen(self.argv + ["queue", "--thread", thread_id, "--message", message],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                      encoding="utf-8", errors="replace", env=external_environment(self.proxy),
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
