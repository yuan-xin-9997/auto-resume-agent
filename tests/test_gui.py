import os
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication
from auto_resume_agent.gui import Window, STYLE
from auto_resume_agent.store import Store
from auto_resume_agent.i18n import LANGUAGES, EN, TRANSLATIONS


def test_five_languages_and_watch_controls(tmp_path):
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    store = Store(tmp_path)
    window = Window(store, start_worker=False)
    tid = str(uuid.uuid4())
    window.rows = [{"id": tid, "name": "Test session", "cwd": str(tmp_path)}]
    window.render()
    window.table.selectRow(0)
    window.watch_selected()
    assert store.watched()[0]["id"] == tid
    window.toggle_enabled()
    assert store.get("enabled") is True
    for key in LANGUAGES:
        window.languages.setCurrentIndex(window.languages.findData(key))
        assert window.toggle.text()
        assert store.get("language", "en") == key
    window.table.selectRow(0)
    window.unwatch_selected()
    assert not store.watched()
    window.agents.setCurrentIndex(1)
    assert window.agent == "opencode" and window.store.agent == "opencode"
    window.rows = [{"id": "ses_gui", "name": "OpenCode fixture", "cwd": str(tmp_path)}]
    window.render()
    window.table.selectRow(0)
    window.watch_selected()
    assert window.store.watched()[0]["id"] == "ses_gui"
    window.toggle_enabled()
    window.agents.setCurrentIndex(0)
    assert window.store is store and not store.get("enabled")
    window.close()
    assert all(set(v) == set(EN) for v in TRANSLATIONS.values())
