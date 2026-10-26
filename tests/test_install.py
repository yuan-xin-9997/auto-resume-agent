from pathlib import Path

import pytest
from auto_resume_agent.install import validate_package


def test_installer_rejects_incomplete_package(tmp_path):
    with pytest.raises(ValueError):
        validate_package(tmp_path)
    (tmp_path / "gui").mkdir()
    (tmp_path / "gui/AutoResumeAgent.exe").write_bytes(b"fixture")
    with pytest.raises(ValueError):
        validate_package(tmp_path)
    (tmp_path / "cli").mkdir()
    (tmp_path / "cli/auto-resume-agent.exe").write_bytes(b"fixture")
    assert validate_package(tmp_path) == tmp_path.resolve()
