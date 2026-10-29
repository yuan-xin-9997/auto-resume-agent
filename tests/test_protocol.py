import json
import queue
import sys
import uuid
import os
import pytest

from auto_resume_agent.protocol import Codex, BackendError
from auto_resume_agent.protocol import external_environment


def test_explicit_codex_proxy_is_inherited_by_helper_without_changing_parent(tmp_path, monkeypatch):
    from auto_resume_agent.backends import create_backend, configuration
    from auto_resume_agent.store import Store
    from auto_resume_agent.window_request import WindowClient
    monkeypatch.setenv("HTTPS_PROXY", "http://old-proxy:8080")
    store = Store(tmp_path)
    store.set("codex_path", sys.executable)
    before = configuration(store)
    store.set("codex_proxy", "http://127.0.0.1:7890")
    backend = create_backend(store, "codex")
    assert configuration(store) != before
    helper = WindowClient(backend)
    assert helper.proxy == backend.proxy == "http://127.0.0.1:7890"
    env = external_environment(helper.proxy)
    assert env["HTTPS_PROXY"] == env["HTTP_PROXY"] == env["https_proxy"] == helper.proxy
    assert os.environ["HTTPS_PROXY"] == "http://old-proxy:8080"
    assert external_environment()["HTTPS_PROXY"] == "http://old-proxy:8080"


@pytest.mark.parametrize("value", ["socks://localhost:1234", "http://user:secret@localhost:1234", "http://localhost:1234/path", "http://localhost:1234?q=1", "http://localhost:bad", "http://localhost"])
def test_invalid_proxy_rejected(value):
    from auto_resume_agent.protocol import proxy_url, BackendError
    with pytest.raises(BackendError, match="codex_invalid_proxy"):
        proxy_url(value)


def test_frozen_child_does_not_inherit_qt_library_paths(tmp_path, monkeypatch):
    import os
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("PATH", str(tmp_path / "PySide6") + os.pathsep + "/usr/bin")
    monkeypatch.setenv("LD_LIBRARY_PATH", str(tmp_path))
    monkeypatch.setenv("LD_LIBRARY_PATH_ORIG", "/system/lib")
    result = external_environment()
    assert result["PATH"] == "/usr/bin"
    assert result["LD_LIBRARY_PATH"] == "/system/lib"


def test_real_subprocess_rpc_and_exact_queue(tmp_path, monkeypatch):
    """Exercise the actual pipes and process boundary, with an isolated fixture agent."""
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    tid = str(uuid.uuid4())
    script = tmp_path / "codex_fixture.py"
    log = tmp_path / "submitted.json"
    script.write_text('''import json, sys
from pathlib import Path
if sys.argv[1] == "queue":
    Path(sys.argv[2]).write_text(json.dumps(sys.argv[3:]))
    raise SystemExit(0)
for line in sys.stdin:
    value=json.loads(line)
    if "id" not in value: continue
    method=value["method"]
    if method=="initialize": result={}
    elif method=="account/rateLimits/read": result={"rateLimits":{"primary":{"usedPercent":10}}}
    elif method=="thread/turns/list": result={"data":[]}
    elif method=="thread/read": result={"thread":{"id":value["params"]["threadId"]}}
    else: result={"data":[],"nextCursor":None}
    print(json.dumps({"id":value["id"],"result":result}),flush=True)
''', encoding="utf-8")
    backend = Codex(sys.executable, timeout=2)
    backend.argv = [sys.executable, str(script)]
    try:
        assert backend.usage()["rateLimits"]["primary"]["usedPercent"] == 10
        assert backend.thread(tid)["id"] == tid
        assert backend.latest(tid) is None
        assert backend.threads()["data"] == []
        # Use a separate tiny command to preserve actual queue argument parsing in the fixture.
        original = backend.argv
        queue_script = tmp_path / "queue_fixture.py"
        queue_script.write_text('import json,sys\nfrom pathlib import Path\nPath('+repr(str(log))+').write_text(json.dumps(sys.argv[1:]))\n')
        backend.argv = [sys.executable, str(queue_script)]
        message = 'Continue & keep literal $() "quotes"; 日本語'
        assert backend.submit(tid, message) == "queued"
        assert json.loads(log.read_text()) == ["queue", "--thread", tid, "--message", message]
        backend.argv = original
    finally:
        backend.close()


@pytest.mark.parametrize("code,expected", [
    (-32601, "codex_experimental_api_missing"),
    (-32600, "codex_protocol_incompatible"),
    (-32602, "codex_protocol_incompatible"),
    (-32700, "codex_protocol_incompatible"),
    (-32000, "protocol_error_-32000"),
])
def test_json_rpc_errors_are_classified_without_raw_text(code, expected):
    backend = object.__new__(Codex)
    backend.sequence = 0
    backend.timeout = 1
    backend.responses = queue.Queue()
    backend.start = lambda: None

    def write(value):
        backend.responses.put({"id": value["id"], "error": {"code": code, "message": "PRIVATE"}})

    backend._write = write
    with pytest.raises(BackendError, match=expected):
        backend.call("thread/turns/list")


def test_codex_response_shape_changes_are_explicit():
    backend = object.__new__(Codex)
    backend.call = lambda *args, **kwargs: {"data": "not-a-list"}
    with pytest.raises(BackendError, match="codex_response_incompatible"):
        backend.latest(str(uuid.uuid4()))

    backend.call = lambda *args, **kwargs: {"thread": None}
    with pytest.raises(BackendError, match="codex_response_incompatible"):
        backend.thread(str(uuid.uuid4()))

    backend.call = lambda *args, **kwargs: {"data": [{"id": "not-a-uuid"}]}
    with pytest.raises(BackendError, match="codex_response_incompatible"):
        backend.threads()

    backend.call = lambda *args, **kwargs: {}
    with pytest.raises(BackendError, match="codex_response_incompatible"):
        backend.usage()
