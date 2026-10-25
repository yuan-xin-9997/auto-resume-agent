import os
import sys
from pathlib import Path


def data_dir():
    if os.environ.get("ARA_HOME"):
        return Path(os.environ["ARA_HOME"]).expanduser().resolve()
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "AutoResumeAgent"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/AutoResumeAgent"
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "auto-resume-agent"


def codex_home():
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
