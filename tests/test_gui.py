import os
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from auto_resume_agent.backends import selected_store
from auto_resume_agent.gui import Window, STYLE
from auto_resume_agent.store import Store
from auto_resume_agent.i18n import LANGUAGES, EN, TRANSLATIONS


def test_five_languages_and_watch_controls(tmp_path):
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(STYLE)
    store = Store(tmp_path)
    store.set("enabled", False)
    window = Window(store, start_worker=False)
    window.set_filter("all")
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
    window.set_filter("all")
    window.rows = [{"id": "ses_gui", "name": "OpenCode fixture", "cwd": str(tmp_path)}]
    window.render()
    window.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
    window.watch_selected()
    assert window.store.watched()[0]["id"] == "ses_gui"
    window.toggle_enabled()
    window.agents.setCurrentIndex(0)
    assert window.store is store and store.get("enabled")
    assert selected_store(store, "opencode").get("enabled") is True
    window.close()
    assert all(set(v) == set(EN) for v in TRANSLATIONS.values())


def test_checkbox_selection_tracks_ids_and_survives_refresh(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Store(tmp_path), start_worker=False)
    window.set_filter("all")
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
    window.set_filter("all")
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


def test_settings_survive_window_and_store_restart(tmp_path):
    from auto_resume_agent import window_keeper
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    first = Window(store, start_worker=False)
    first.languages.setCurrentIndex(first.languages.findData("zh-CN"))
    first.intervals["codex"].setValue(45)
    first.intervals["opencode"].setValue(90)
    first.auto_watch.setChecked(False)
    first.keeper_toggle.setChecked(True)
    first.codex_proxy.setText("http://127.0.0.1:7890")
    first.opencode_url.setText("http://127.0.0.1:4097")
    first.opencode_directory.setText(str(tmp_path))
    first.save()
    store.set("enabled", True)
    tid = str(uuid.uuid4())
    store.watch(tid)
    first.close()
    restarted = Store(tmp_path)
    second = Window(restarted, start_worker=False)
    assert second.intervals["codex"].value() == 45
    assert second.intervals["opencode"].value() == 90
    assert second.language == "zh-CN"
    assert not second.auto_watch.isChecked()
    assert second.keeper_toggle.isChecked() and window_keeper.enabled(restarted)
    assert second.codex_proxy.text() == "http://127.0.0.1:7890"
    assert second.opencode_url.text() == "http://127.0.0.1:4097"
    assert second.opencode_directory.text() == str(tmp_path)
    assert restarted.get("enabled") is True
    assert restarted.watched()[0]["id"] == tid
    second.close()


def test_switching_agents_saves_connection_fields_and_keeps_enabled_state(tmp_path):
    app = QApplication.instance() or QApplication([])
    base = Store(tmp_path)
    base.set("agent", "codex")
    base.set("enabled", True)
    opencode = selected_store(base, "opencode")
    opencode.set("enabled", True)
    window = Window(base, start_worker=False)
    window.opencode_url.setText("http://127.0.0.1:28894")
    window.opencode_directory.setText(str(tmp_path))
    window.codex_proxy.setText("http://127.0.0.1:7890")
    assert window.dirty and window.save_button.isEnabled()
    window.agents.setCurrentIndex(window.agents.combo.findData("opencode"))
    assert window.agent == "opencode" and base.get("agent") == "opencode"
    assert base.get("opencode_url") == "http://127.0.0.1:28894"
    assert base.get("opencode_directory") == str(tmp_path)
    assert base.get("codex_proxy") == "http://127.0.0.1:7890"
    assert not window.dirty and not window.save_button.isEnabled()
    window.store.set("enabled", True)
    window.agents.setCurrentIndex(window.agents.combo.findData("codex"))
    assert window.agent == "codex" and base.get("enabled") is True
    assert selected_store(base, "opencode").get("enabled") is True
    window.close()


def test_invalid_connection_blocks_agent_switch(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    base = Store(tmp_path)
    base.set("agent", "codex")
    base.set("enabled", True)
    window = Window(base, start_worker=False)
    window.opencode_url.setText("http://example.com/path")
    warnings = []
    monkeypatch.setattr("auto_resume_agent.gui.QMessageBox.warning",
                        lambda *args, **kwargs: warnings.append(args))
    window.agents.setCurrentIndex(window.agents.combo.findData("opencode"))
    assert window.agent == "codex" and base.get("agent") == "codex"
    assert window.agents.combo.currentData() == "codex"
    assert window.agents.buttons[0].isChecked() and not window.agents.buttons[1].isChecked()
    assert warnings and window.dirty
    window.close()


def test_quota_duration_labels_all_languages():
    from auto_resume_agent.i18n import duration_label
    assert duration_label(300, "zh-CN") == "5 小时"
    assert duration_label(10080, "zh-CN") == "一周"
    assert duration_label(43200, "zh-CN") == "一个月"
    assert duration_label(300) == "5 hours"
    assert duration_label(10080) == "1 week"
    assert duration_label(43200) == "1 month"
    assert duration_label(60, "zh-CN") == "60 分钟"
    for language in LANGUAGES:
        assert "300" not in duration_label(300, language)
        assert "10080" not in duration_label(10080, language)
        assert "43200" not in duration_label(43200, language)

def test_empty_quota_card_uses_pending_status(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Store(tmp_path), start_worker=False)
    card = window.build_quota_card(None, None)
    texts = [label.text() for label in card.findChildren(type(window.connection))]
    assert window.text("quota_pending") in texts
    window.close()


def test_default_filter_is_watching(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Store(tmp_path), start_worker=False)
    assert window.filter_key == "filter_watching"
    assert window.filter_buttons["filter_watching"].isChecked()
    assert not window.filter_buttons["all"].isChecked()
    window.close()


def test_initial_connection_state_is_connecting(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Store(tmp_path), start_worker=False)
    assert window.connection.text() == window.text("connecting")
    assert window.connection_tone == "accent"
    window.close()


def test_refresh_gives_immediate_feedback_and_timeout_hint(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Store(tmp_path), start_worker=False)
    requests = []

    class Worker:
        def request(self, kind, value=None):
            requests.append((kind, value))

    window.worker = Worker()
    window.refresh()
    assert requests == [("refresh", None), ("threads", None)]
    assert window.refreshing
    assert window.connection.text() == window.text("refreshing")
    window.refresh()
    assert requests == [("refresh", None), ("threads", None)]
    window.refresh_slow()
    assert window.connection.text() == window.text("refresh_slow")
    window.refresh_timeout()
    assert not window.refreshing
    assert window.connection.text() == window.text("refresh_timeout")
    window.refresh_hint_timer.stop()
    window.refresh_timeout_timer.stop()
    window.worker = None
    window.refresh()
    assert window.connection.text() == window.text("refresh_unavailable")
    window.close()


def test_periodic_refresh_uses_non_destructive_sync(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    window = Window(store, start_worker=False)
    requests = []

    class Worker:
        def request(self, kind, value=None):
            requests.append((kind, value))

    window.worker = Worker()
    window.loading = False
    window.periodic_refresh()
    assert requests == [("sync", None)]
    window.loading = True
    window.periodic_refresh()
    assert requests == [("sync", None)]
    window.worker = None
    window.close()


def test_session_search_and_persistent_activity_names(tmp_path):
    app = QApplication.instance() or QApplication([])
    store = Store(tmp_path)
    window = Window(store, start_worker=False)
    window.set_filter("all")
    a, b = str(uuid.uuid4()), str(uuid.uuid4())
    window.rows = [{"id": a, "name": "Alpha report", "cwd": "/work/Research"},
                   {"id": b, "name": "Beta", "cwd": "/work/Other"}]
    store.event(a, "detected")
    window.render()
    window.select_all.setChecked(True)
    window.search.setText("ALPHA")
    assert window.table.rowCount() == 1
    assert window.selected() == [a]
    window.watch_selected()
    assert [r['id'] for r in store.watched()] == [a]
    window.select_all.setChecked(False)
    assert b in window.checked_ids and a not in window.checked_ids
    assert not window.watch_button.isEnabled()
    window.search.setText("research")
    assert window.table.item(0, 1).data(Qt.ItemDataRole.UserRole) == a
    window.search.setText(b)
    assert window.table.rowCount() == 1
    assert window.selected() == [b]
    window.search.clear()
    assert window.table.rowCount() == 2
    assert window.events.item(0, 1).text() == "Alpha report\n" + a
    window.close()
    reopened = Window(Store(tmp_path), start_worker=False)
    assert reopened.events.item(0, 1).text() == "Alpha report\n" + a
    reopened.close()
