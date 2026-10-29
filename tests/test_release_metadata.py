import tomllib
from pathlib import Path

from auto_resume_agent import __version__

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_version_install_names_and_evidence_match():
    project = tomllib.loads(read("pyproject.toml"))["project"]
    assert project["version"] == __version__
    readme = read("README.md")
    for suffix in ("windows-x64.zip", "linux-x64.tar.gz", "macos-arm64.tar.gz", "macos-x64.tar.gz"):
        assert f"AutoResumeAgent-v{__version__}-{suffix}" in readme
    assert f"# Auto Resume Agent v{__version__}" in read("docs/RELEASE_NOTES.md")
    assert f"## v{__version__}" in read("docs/TESTING.md")
    assert f"## v{__version__}" in read("docs/COMPATIBILITY.md")


def test_documented_backend_baselines_are_consistent():
    readme = read("README.md")
    compatibility = read("docs/COMPATIBILITY.md")
    testing = read("docs/TESTING.md")
    for text in (readme, compatibility, testing):
        assert "0.163.0" in text
        assert "1.19.3" in text


def test_release_license_material_is_present():
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "licenses/GPL-3.0.txt", "licenses/LGPL-3.0.txt"):
        assert (ROOT / name).is_file()
    notices = read("THIRD_PARTY_NOTICES.md")
    assert "PySide6" in notices and "LGPLv3" in notices and "PyInstaller" in notices
