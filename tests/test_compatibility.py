import json
import uuid

from auto_resume_agent import cli
from auto_resume_agent.protocol import BackendError

TID = str(uuid.uuid4())


class HealthyCodex:
    def start(self):
        pass

    def usage(self):
        return {"rateLimits": {"primary": {"usedPercent": 10, "resetsAt": 1_800_000_100}}}

    def threads(self):
        return {"data": [], "nextCursor": None}

    def thread(self, tid):
        raise AssertionError("doctor must not invent a session")

    def latest(self, tid):
        raise AssertionError("doctor must not invent a session")

    def submit(self, tid, message):
        raise AssertionError("doctor must never submit")

    def close(self):
        pass


class IncompatibleCodex(HealthyCodex):
    def threads(self):
        return {"data": [{"id": TID}], "nextCursor": None}

    def thread(self, tid):
        raise BackendError("codex_experimental_api_missing")


class MalformedCodex(HealthyCodex):
    def threads(self):
        return {"data": [None], "nextCursor": None}


def test_doctor_reports_compatibility_without_submitting(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "create_backend", lambda base, agent: HealthyCodex())
    assert cli.main(["--home", str(tmp_path), "doctor"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["compatible"] is True
    assert report["checks"]["latest_turn"] == "not_tested_no_sessions"
    assert report["submission_tested"] is False
    assert report["automatic_sending"] == "available_when_enabled"


def test_doctor_blocks_sending_on_missing_experimental_method(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "create_backend", lambda base, agent: IncompatibleCodex())
    assert cli.main(["--home", str(tmp_path), "doctor"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["compatible"] is False
    assert report["app_server"] == "incompatible"
    assert report["error"] == "codex_experimental_api_missing"
    assert report["checks"]["history"] == "failed"
    assert report["automatic_sending"] == "blocked"
    assert report["submission_tested"] is False


def test_doctor_treats_a_malformed_history_shape_as_incompatible(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "create_backend", lambda base, agent: MalformedCodex())
    assert cli.main(["--home", str(tmp_path), "doctor"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["compatible"] is False
    assert report["app_server"] == "incompatible"
    assert report["error"] == "codex_response_incompatible"
    assert report["automatic_sending"] == "blocked"
