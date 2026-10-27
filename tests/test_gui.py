import os
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from auto_resume_agent.gui import Window, STYLE
from auto_resume_agent.store import Store
from auto_resume_agent.i18n import LANGUAGES, EN, TRANSLATIONS


def test_five_languages_and_watch_controls(tmp_path):
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    store = Store(tmp_path)
    window = Window(store, start_worker=False)
    assert window.auto_watch.isChecked()
    window.auto_watch.setChecked(False)
    assert store.get("auto_watch_quota") is False
    window.auto_watch.setChecked(True)
    assert store.get("auto_watch_quota") is True
    tid = str(uuid.uuid4())
    window.rows = [{"id": tid, "name": "Test session", "cwd": str(tmp_path)}]
    window.render()
    assert not window.keeper_toggle.isChecked()
    window.keeper_toggle.setChecked(True)
    from auto_resume_agent import window_keeper
    assert window_keeper.enabled(store)
    window.keeper_toggle.setChecked(False)
    assert not window_keeper.enabled(store)
    window.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    window.watch_selected()
    assert store.watched()[0]["id"] == tid
    window.toggle_enabled()
    assert store.get("enabled") is True
    for key in LANGUAGES:
        window.languages.setCurrentIndex(window.languages.findData(key))
        assert window.toggle.text()
        assert store.get("language", "en") == key
    window.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    window.unwatch_selected()
    assert not store.watched()
    window.agents.setCurrentIndex(1)
    assert window.agent == "opencode" and window.store.agent == "opencode"
    window.rows = [{"id": "ses_gui", "name": "OpenCode fixture", "cwd": str(tmp_path)}]
    window.render()
    window.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    window.watch_selected()
    assert window.store.watched()[0]["id"] == "ses_gui"
    window.toggle_enabled()
    window.agents.setCurrentIndex(0)
    assert window.store is store and not store.get("enabled")
    window.close()
    assert all(set(v) == set(EN) for v in TRANSLATIONS.values())


def test_checkbox_selection_tracks_ids_and_survives_refresh(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Store(tmp_path), start_worker=False)
    ids = [str(uuid.uuid4()) for _ in range(3)]
    window.rows = [{"id": tid, "name": "Session " + str(i), "cwd": str(tmp_path)} for i, tid in enumerate(ids)]
    window.render()
    assert not window.watch_button.isEnabled()
    window.table.item(1, 0).setCheckState(Qt.CheckState.Checked)
    assert window.selected() == [ids[1]]
    window.rows.reverse()
    window.render()
    assert window.selected() == [ids[1]]
    assert window.table.item(1, 0).checkState() == Qt.CheckState.Checked
    window.languages.setCurrentIndex(window.languages.findData("zh-CN"))
    assert window.selected() == [ids[1]]
    window.watch_selected()
    assert [r["id"] for r in window.store.watched()] == [ids[1]]
    window.select_all.setChecked(True)
    assert set(window.selected()) == set(ids)
    # A provider may repeat IDs in a page: all-selected must still toggle off.
    window.rows.append(dict(window.rows[0]))
    window.render()
    assert window.select_all.isChecked()
    window.select_all.setChecked(False)
    assert window.selected() == []
    window.rows.pop()
    assert not window.watch_button.isEnabled()
    # A row highlight is not a checked target; unchecked rows cannot be acted on accidentally.
    window.table.selectRow(0)
    assert window.selected() == []
    window.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    removed = window.rows.pop(0)["id"]
    window.render()
    assert removed not in window.checked_ids
    header = window.table.horizontalHeader().defaultAlignment()
    assert header & Qt.AlignmentFlag.AlignLeft
    for col in (1, 2, 3):
        assert window.table.item(0, col).textAlignment() & Qt.AlignmentFlag.AlignLeft
        assert window.table.item(0, col).textAlignment() & Qt.AlignmentFlag.AlignTop
    window.close()


def test_rewatch_cancelled_recovery_shows_watching_without_resetting_history(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    window = Window(store, start_worker=False)
    window.languages.setCurrentIndex(window.languages.findData("zh-CN"))
    tid, turn = str(uuid.uuid4()), str(uuid.uuid4())
    store.watch(tid)
    with store.db() as db:
        db.execute("INSERT INTO recoveries(id,thread_id,turn_id,kind,state,due,created) VALUES (?,?,?,?,?,?,?)",
                   ("fixture", tid, turn, "usage_limit", "waiting", 100, 90))
    window.rows = [{"id": tid, "name": "Rewatch fixture", "cwd": str(tmp_path)}]
    window.render()
    window.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    window.unwatch_selected()
    assert window.table.item(0, 3).text() == window.text("cancelled")
    assert not store.watched()
    cancelled = store.records()
    window.watch_selected()
    assert [r["id"] for r in store.watched()] == [tid]
    assert window.table.item(0, 3).text() == "监控中"
    assert not window.table.item(0, 3).toolTip()
    window.render()
    assert window.table.item(0, 3).text() == "监控中"
    assert store.records() == cancelled  # Never revive cancelled/delivered requests.
    window.close()


def test_quota_duration_labels_all_languages():
    from auto_resume_agent.i18n import duration_label
    assert duration_label(300, "zh-CN") == "5 小时"
    assert duration_label(10080, "zh-CN") == "一周"
    assert duration_label(300) == "5 hours"
    assert duration_label(10080) == "1 week"
    assert duration_label(60, "zh-CN") == "60 分钟"
    for language in LANGUAGES:
        assert "300" not in duration_label(300, language)
        assert "10080" not in duration_label(10080, language)
