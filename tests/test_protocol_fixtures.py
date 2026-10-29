import json
from pathlib import Path

from auto_resume_agent.model import category, usage
from auto_resume_agent.opencode import normalize

FIXTURES = Path(__file__).parent / "fixtures" / "protocol"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_codex_0163_synthetic_shape_samples():
    quota = usage(load("codex-0.163.0-rate-limits.json"))
    assert quota["available"] is False
    assert quota["reset_at"] == 1800604800
    page = load("codex-0.163.0-thread-list.json")
    assert page["data"][0]["source"] == "cli"
    turn = load("codex-0.163.0-latest-turn.json")["data"][0]
    assert category(turn) == "usage_limit"


def test_opencode_1193_synthetic_shape_samples():
    health = load("opencode-1.19.3-health.json")
    assert health["healthy"] is True and health["version"] == "1.19.3"
    session = load("opencode-1.19.3-session.json")
    assert session["id"].startswith("ses_") and not session.get("parentID")
    turn = normalize(load("opencode-1.19.3-message.json")["info"])
    assert turn["status"] == "failed"
    assert turn["error"]["codexErrorInfo"] == "rateLimitExceeded"
    assert turn["retryAt"] == 1800000030
    # The same HTTP 429 is terminal when the body is a billing denial.
    billing = normalize(load("opencode-1.19.3-billing-message.json")["info"])
    assert billing["status"] == "completed"
