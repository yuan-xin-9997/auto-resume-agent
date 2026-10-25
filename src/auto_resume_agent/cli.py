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


def main(argv=None):
    parser = argparse.ArgumentParser(prog="auto-resume-agent", description="Codex quota monitoring and exact-session recovery")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--codex", help="Path to Codex executable")
    parser.add_argument("--home", help="Auto Resume Agent state directory")
    sub = parser.add_subparsers(dest="action")
    for name in ("gui", "usage", "sessions", "status", "pause", "enable", "watch", "check", "doctor"):
        sub.add_parser(name)
    for name in ("add", "remove", "cancel"):
        sub.add_parser(name).add_argument("id")
    args = parser.parse_args(argv)
    store = Store(args.home)
    if args.codex:
        store.set("codex_path", args.codex)
    if args.action in (None, "gui"):
        from .gui import main as gui_main
        return gui_main(store)
    if args.action in ("enable", "pause"):
        store.set("enabled", args.action == "enable")
        print(json.dumps({"enabled": store.get("enabled")}))
        return 0
    if args.action == "add":
        try:
            store.watch(args.id)
        except ValueError:
            parser.error("Expected an exact session UUID")
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
                          "usage": store.get("usage"), "recoveries": store.records()}, indent=2))
        return 0
    backend = None
    try:
        backend = Codex(store.get("codex_path") or None)
        if args.action == "usage":
            print(json.dumps(usage(backend.usage()), indent=2))
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
            snapshot = usage(backend.usage())
            # Verify the exact methods used by the monitor without submitting anything.
            page = backend.threads()
            compatible = True
            if page.get("data"):
                tid = page["data"][0]["id"]
                backend.thread(tid)
                backend.latest(tid)
            print(json.dumps({"app_server": "ok", "history": compatible, "quota_known": snapshot["available"] is not None,
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
