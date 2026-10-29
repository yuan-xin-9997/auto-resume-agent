import argparse
import json
import signal
import sys
import threading

from . import __version__
from .engine import Engine
from .model import usage
from .protocol import Codex, BackendError, is_compatibility_error
from .store import Store
from .backends import create_backend, selected_store, snapshot
from . import window_keeper


def diagnose(backend, agent, state_dir):
    """Read-only adapter check; never submits a continuation."""
    shape_error = "opencode_response_incompatible" if agent == "opencode" else "codex_response_incompatible"
    report = {"agent": agent, "app_server": "ok", "compatible": True, "checks": {},
              "quota_known": False, "state_dir": str(state_dir),
              "submission_tested": False, "automatic_sending": "available_when_enabled"}

    def failed(step, error):
        report["checks"][step] = "failed"
        report["compatible"] = False
        report["app_server"] = "incompatible" if is_compatibility_error(error) else "unavailable"
        report["error"] = str(error)
        report["automatic_sending"] = "blocked"
        return report

    try:
        backend.start()
        report["checks"]["start"] = "ok"
    except BackendError as error:
        return failed("start", error)
    try:
        quota = snapshot(backend)
        report["quota_known"] = quota.get("available") is not None
        report["checks"]["usage"] = "ok"
    except BackendError as error:
        return failed("usage", error)
    try:
        page = backend.threads()
        rows = page.get("data", []) if isinstance(page, dict) else None
        if not isinstance(rows, list):
            raise BackendError(shape_error)
        report["checks"]["thread_list"] = "ok"
        if rows:
            tid = rows[0].get("id") if isinstance(rows[0], dict) else None
            if not tid:
                raise BackendError(shape_error)
            backend.thread(tid)
            report["checks"]["thread_read"] = "ok"
            backend.latest(tid)
            report["checks"]["latest_turn"] = "ok"
        else:
            report["checks"]["thread_read"] = "not_tested_no_sessions"
            report["checks"]["latest_turn"] = "not_tested_no_sessions"
    except BackendError as error:
        return failed("history", error)
    except (KeyError, TypeError, ValueError):
        return failed("history", BackendError(shape_error))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="auto-resume-agent", description="Codex and OpenCode session recovery")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--codex", help="Path to Codex executable")
    parser.add_argument("--codex-proxy", help="HTTP(S) proxy origin with explicit port; empty clears it")
    parser.add_argument("--home", help="Auto Resume Agent state directory")
    parser.add_argument("--agent", choices=("codex", "opencode"), default=None)
    parser.add_argument("--opencode-url", help="OpenCode HTTP server URL (saved)")
    parser.add_argument("--opencode-directory", help="OpenCode workspace directory (saved)")
    sub = parser.add_subparsers(dest="action")
    for name in ("gui", "usage", "sessions", "status", "pause", "enable", "watch", "check", "doctor", "install"):
        sub.add_parser(name)
    for name in ("add", "remove", "cancel"):
        sub.add_parser(name).add_argument("id")
    sub.add_parser("window-keeper", help="Codex five-hour window first request (default off)").add_argument(
        "mode", choices=("on", "off", "status"), nargs="?", default="status")
    sub.add_parser("auto-watch", help="Discover quota-exhausted Codex sessions (default on)").add_argument(
        "mode", choices=("on", "off", "status"), nargs="?", default="status")
    args = parser.parse_args(argv)
    if args.action == "install":
        from .install import install
        try:
            print(json.dumps(install(), indent=2))
        except (OSError, ValueError) as error:
            print(json.dumps({"error": str(error)}), file=sys.stderr)
            return 1
        return 0
    if args.opencode_url is not None:
        from .opencode import endpoint
        try:
            args.opencode_url = endpoint(args.opencode_url)
        except BackendError as error:
            parser.error(str(error))
    base = Store(args.home)
    store = base
    if args.codex:
        store.set("codex_path", args.codex)
    if args.codex_proxy is not None:
        from .protocol import proxy_url
        try:
            store.set("codex_proxy", proxy_url(args.codex_proxy) or "")
        except BackendError as error:
            parser.error(str(error))
    for option in ("opencode_url", "opencode_directory"):
        if getattr(args, option) is not None:
            base.set(option, getattr(args, option))
    if args.action in (None, "gui"):
        if args.agent:
            base.set("agent", args.agent)
        from .gui import main as gui_main
        return gui_main(base)
    agent = args.agent or "codex"
    try:
        store = selected_store(base, agent)
    except BackendError as error:
        parser.error(str(error))
    if args.action == "auto-watch":
        if agent != "codex":
            parser.error("auto-watch is available for Codex only")
        if args.mode != "status":
            base.set("auto_watch_quota", args.mode == "on")
        print(json.dumps({"enabled": base.get("auto_watch_quota", True)}))
        return 0
    if args.action == "window-keeper":
        if agent != "codex":
            parser.error("window-keeper is available for Codex only")
        if args.mode != "status":
            window_keeper.set_enabled(store, args.mode == "on")
        print(json.dumps(window_keeper.status(store), indent=2))
        return 0
    if args.action in ("enable", "pause"):
        store.set("enabled", args.action == "enable")
        print(json.dumps({"enabled": store.get("enabled")}))
        return 0
    if args.action == "add":
        try:
            store.watch(args.id)
        except ValueError:
            parser.error("Expected an exact session ID (Codex UUID or OpenCode ses_ ID)")
        print(json.dumps({"watching": args.id}))
        return 0
    if args.action == "remove":
        store.unwatch(args.id)
        return 0
    if args.action == "cancel":
        print(json.dumps({"cancelled": store.cancel(args.id)}))
        return 0
    if args.action == "status":
        print(json.dumps({"enabled": store.get("enabled", False), "watched": store.watched(),
                          "auto_watch_quota": base.get("auto_watch_quota", True) if agent == "codex" else None,
                          "usage": store.get("usage"), "last_error": store.get("last_error"), "recoveries": store.records(),
                          "window_keeper": window_keeper.status(store) if agent == "codex" else None}, indent=2))
        return 0
    backend = None
    try:
        backend = create_backend(base, agent)
        if args.action == "usage":
            print(json.dumps(snapshot(backend), indent=2))
        elif args.action == "sessions":
            cursor = None
            while True:
                page = backend.threads(cursor)
                for row in page.get("data", []):
                    print(json.dumps({"id": row["id"], "name": row.get("name"), "cwd": row.get("cwd")}, ensure_ascii=False))
                cursor = page.get("nextCursor")
                if not cursor:
                    break
        elif args.action == "doctor":
            # Verify the exact methods used by the monitor without submitting anything.
            report = diagnose(backend, agent, store.root)
            print(json.dumps(report, indent=2))
            return 0 if report["compatible"] else 1
        else:
            engine = Engine(store, backend)
            stop = threading.Event()
            signal.signal(signal.SIGINT, lambda *_: stop.set())
            if hasattr(signal, "SIGTERM"):
                signal.signal(signal.SIGTERM, lambda *_: stop.set())
            while not stop.is_set():
                try:
                    result = engine.tick()
                except (BackendError, OSError, ValueError) as error:
                    backend.close()
                    result = {"error": str(error) if isinstance(error, BackendError) else "local_io_error", "delay": 10}
                print(json.dumps(result), flush=True)
                if args.action == "check":
                    return 1 if result.get("error") else 0
                stop.wait(result["delay"])
    except (BackendError, OSError) as error:
        print(json.dumps({"error": str(error) if isinstance(error, BackendError) else "local_io_error"}), file=sys.stderr)
        return 1
    finally:
        if backend:
            backend.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
