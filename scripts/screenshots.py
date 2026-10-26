"""Render illustrative product screenshots without connecting to personal sessions."""
import os
import tempfile
import time
import uuid
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from auto_resume_agent.gui import Window, STYLE
from auto_resume_agent.store import Store

app = QApplication([])
if os.name == "nt":
    # Qt's offscreen platform does not enumerate Windows system fonts.
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for filename in ("segoeui.ttf", "segoeuib.ttf", "msyh.ttc", "msyhbd.ttc", "malgun.ttf", "msgothic.ttc"):
        if (fonts / filename).is_file():
            QFontDatabase.addApplicationFont(str(fonts / filename))
app.setStyleSheet(STYLE)
output = Path(__file__).resolve().parents[1] / "docs/screenshots"
output.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as root:
    store = Store(root)
    now = time.time()
    store.set("usage", {"available": False, "checked_at": now, "reset_at": now+1200, "windows": [
        {"bucket": "codex", "window": "primary", "used_percent": 100, "minutes": 300, "reset_at": now+1200},
        {"bucket": "codex", "window": "secondary", "used_percent": 42, "minutes": 10080, "reset_at": now+86400}]})
    store.set("enabled", True)
    rows = [{"id": str(uuid.uuid5(uuid.NAMESPACE_DNS, str(i))), "name": name, "cwd": "/projects/"+project}
            for i, (name, project) in enumerate([("Build the next release", "workspace"),
                ("Review the API changes", "api-service"), ("Explore a new idea", "playground")])]
    for row in rows[:2]:
        store.watch(row["id"])
    with store.db() as db:
        db.execute("INSERT INTO recoveries(id,thread_id,turn_id,kind,state,due,created,detail) VALUES (?,?,?,?,?,?,?,?)",
                   ("illustrative", rows[0]["id"], str(uuid.uuid4()), "usage_limit", "waiting", now+1202, now, "waiting_reset"))
    window = Window(store, start_worker=False)
    window.rows = rows
    window.show()
    for language, filename in [("en", "dashboard.png"), ("zh-CN", "dashboard.zh-CN.png")]:
        window.languages.setCurrentIndex(window.languages.findData(language))
        window.render()
        window.connection.setText(window.text("ready"))
        app.processEvents()
        window.grab().save(str(output / filename))
    from auto_resume_agent import window_keeper
    previous = store.get("usage")
    store.set("usage", {**previous, "available": True, "windows": [
        {**w, "used_percent": 23} if w["window"] == "primary" else w for w in previous["windows"]]})
    window_keeper.set_enabled(store, True)
    store.set(window_keeper.key(store, "due"), now+1200)
    window.render()
    app.processEvents()
    window.grab().save(str(output / "dashboard.window-keeper.zh-CN.png"))
    window_keeper.set_enabled(store, False)
    window.agents.setCurrentIndex(1)
    window.rows = [{"id": "ses_example" + str(i), "name": r["name"], "cwd": r["cwd"]} for i, r in enumerate(rows)]
    window.store.set("usage", {"available": None, "windows": [], "checked_at": now, "reason": "quota_not_exposed"})
    window.store.watch("ses_example0")
    window.render()
    window.connection.setText(window.text("ready").replace("Codex", "OpenCode"))
    app.processEvents()
    window.grab().save(str(output / "dashboard.opencode.zh-CN.png"))
    window.close()
print(output)
