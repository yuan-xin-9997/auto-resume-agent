import json
import sys
import uuid

from auto_resume_agent.protocol import Codex


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
