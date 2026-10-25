"""Render the repository's vector logo to platform icon formats."""
import io
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt
from PIL import Image

app = QApplication.instance() or QApplication([])
assets = Path(__file__).resolve().parents[1] / "src/auto_resume_agent/assets"
renderer = QSvgRenderer(str(assets / "icon.svg"))
canvas = QImage(1024, 1024, QImage.Format.Format_ARGB32)
canvas.fill(Qt.GlobalColor.transparent)
painter = QPainter(canvas)
renderer.render(painter)
painter.end()
canvas.save(str(assets / "icon.png"))
image = Image.open(assets / "icon.png")
image.save(assets / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
image.save(assets / "icon.icns")
print("Created PNG, ICO and ICNS icons")
