import hashlib
import json

from .opencode import OpenCode, endpoint
from .protocol import Codex
from .store import Store


def configuration(base):
    return (base.get("agent", "codex"), base.get("codex_path", ""),
            base.get("opencode_url", "http://127.0.0.1:4096"), base.get("opencode_directory", ""),
            base.get("codex_proxy", ""), base.get("codex_interval", 30), base.get("opencode_interval", 30))


def selected_store(base, agent):
    if agent == "codex":
        return base
    url = endpoint(base.get("opencode_url", "http://127.0.0.1:4096"))
    directory = base.get("opencode_directory", "")
    identity = json.dumps([url, directory])
    key = hashlib.sha256(identity.encode()).hexdigest()[:20]
    store = Store(base.root / "opencode" / key, agent="opencode", source=identity)
    store.set("poll_interval", base.get("opencode_interval", 30))
    return store


def create_backend(base, agent):
    if agent == "opencode":
        return OpenCode(base.get("opencode_url", "http://127.0.0.1:4096"), base.get("opencode_directory", ""))
    return Codex(base.get("codex_path") or None, proxy=base.get("codex_proxy") or None)


def snapshot(backend):
    from .model import usage
    value = backend.usage()
    return value if isinstance(backend, OpenCode) else usage(value)
