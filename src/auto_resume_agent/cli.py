import argparse
import json
import signal
import sys
import threading

from . import __version__
from .engine import Engine
from .model import usage
from .protocol import Codex, BackendError
from .store import Store
from .backends import create_backend, selected_store, snapshot
from . import window_keeper


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
        store.update(args.id, "cancelled")
        return 0
    if args.action == "status":
        print(json.dumps({"enabled": store.get("enabled", False), "watched": store.watched(),
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
            backend.start()
            quota = snapshot(backend)
            # Verify the exact methods used by the monitor without submitting anything.
            page = backend.threads()
            compatible = True
            if page.get("data"):
                tid = page["data"][0]["id"]
                backend.thread(tid)
                backend.latest(tid)
            print(json.dumps({"agent": agent, "app_server": "ok", "history": compatible, "quota_known": quota["available"] is not None,
                              "state_dir": str(store.root), "submission_tested": False}, indent=2))
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
