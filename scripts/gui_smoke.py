"""Native window/event-loop smoke test; no agent calls or personal session access."""
import json
import platform
import tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from auto_resume_agent.gui import Window, STYLE
from auto_resume_agent.store import Store

app = QApplication([])
app.setStyleSheet(STYLE)
with tempfile.TemporaryDirectory() as root:
    window = Window(Store(root), start_worker=False)
    window.show()
    def verify():
        assert window.isVisible()
        for key in ("en", "zh-CN", "zh-TW", "ja", "ko"):
            window.languages.setCurrentIndex(window.languages.findData(key))
            assert window.toggle.text()
        print(json.dumps({"os": platform.platform(), "qt_platform": app.platformName(), "native_window": True,
                          "five_languages": True}), flush=True)
        window.close()
        app.quit()
    QTimer.singleShot(2000, verify)
    app.exec()
