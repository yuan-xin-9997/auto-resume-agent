"""Item delegates that paint the denser session and activity tables."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QStyledItemDelegate

from . import theme as ui_theme
from .widgets import paint_row_background


def _color(values, key, alpha=None):
    value = values[key]
    if isinstance(value, str) and value.startswith("rgba("):
        parts = value[5:-1].split(",")
        color = QColor(int(parts[0]), int(parts[1]), int(parts[2]))
        color.setAlphaF(float(parts[3]) if len(parts) > 3 else 1.0)
    else:
        color = QColor(value)
    if alpha is not None:
        color.setAlphaF(alpha)
    return color


class SessionDelegate(QStyledItemDelegate):
    def __init__(self, theme="light", parent=None):
        super().__init__(parent)
        self.theme = theme

    def paint(self, painter, option, index):
        values = ui_theme.palette(self.theme)
        paint_row_background(painter, option, self.theme)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        title, _, subtitle = text.partition("\n")
        painter.save()
        painter.setClipRect(option.rect)
        rect = option.rect.adjusted(12, 8, -10, -6)
        title_font = QFont(option.font)
        title_font.setPixelSize(13)
        title_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(title_font)
        painter.setPen(QColor(values["text"]))
        metrics = QFontMetrics(title_font)
        title = metrics.elidedText(title, Qt.TextElideMode.ElideRight, max(10, rect.width()))
        x, y = rect.x(), rect.y()
        painter.drawText(x, y + metrics.ascent(), title)
        if subtitle:
            sub_font = QFont(option.font)
            sub_font.setPixelSize(11)
            painter.setFont(sub_font)
            painter.setPen(QColor(values["muted"]))
            sub_metrics = QFontMetrics(sub_font)
            subtitle = sub_metrics.elidedText(subtitle, Qt.TextElideMode.ElideRight, max(10, rect.width()))
            painter.drawText(x, y + metrics.height() + 3 + sub_metrics.ascent(), subtitle)
        painter.restore()


class ProjectDelegate(QStyledItemDelegate):
    def __init__(self, theme="light", parent=None):
        super().__init__(parent)
        self.theme = theme
        self.icon = ui_theme.icon("folder", theme, size=14)

    def paint(self, painter, option, index):
        values = ui_theme.palette(self.theme)
        paint_row_background(painter, option, self.theme)
        title = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        painter.save()
        painter.setClipRect(option.rect)
        icon_rect = option.rect.adjusted(12, 0, 0, 0)
        self.icon.paint(painter, icon_rect.x(), icon_rect.y() + (icon_rect.height() - 14) // 2, 14, 14)
        font = QFont(option.font)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor(values["muted"]))
        metrics = QFontMetrics(font)
        title = metrics.elidedText(title or "—", Qt.TextElideMode.ElideRight, max(10, option.rect.width() - 38))
        painter.drawText(option.rect.x() + 32,
                         option.rect.y() + (option.rect.height() + metrics.ascent() - metrics.descent()) // 2,
                         title)
        painter.restore()


class StatusDelegate(QStyledItemDelegate):
    TONES = {
        "watching": "accent",
        "waiting": "warning",
        "queued": "info",
        "sending": "info",
        "accepted": "info",
        "uncertain": "danger",
        "attention": "danger",
        "progressed": "success",
        "superseded": "neutral",
        "cancelled": "neutral",
        "unwatched": "neutral",
        "unknown": "neutral",
    }

    def __init__(self, theme="light", parent=None):
        super().__init__(parent)
        self.theme = theme

    def paint(self, painter, option, index):
        values = ui_theme.palette(self.theme)
        paint_row_background(painter, option, self.theme)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        state = str(index.data(Qt.ItemDataRole.UserRole + 1) or "neutral")
        tone = self.TONES.get(state, "neutral")
        fg = _color(values, "neutral" if tone == "neutral" else tone)
        bg = _color(values, "neutralSoft" if tone == "neutral" else tone + "Soft")
        font = QFont(option.font)
        font.setPixelSize(11)
        font.setWeight(QFont.Weight.DemiBold)
        metrics = QFontMetrics(font)
        width = max(24, min(option.rect.width() - 24, metrics.horizontalAdvance(text) + 20))
        height = 22
        pill = QRectF(option.rect.x() + 12, option.rect.y() + (option.rect.height() - height) / 2, width, height)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(pill, 9, 9)
        painter.setFont(font)
        painter.setPen(fg)
        painter.drawText(pill.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignCenter,
                         metrics.elidedText(text, Qt.TextElideMode.ElideRight, max(10, int(width) - 16)))
        painter.restore()


class EventDelegate(QStyledItemDelegate):
    TONES = {
        "detected": "warning",
        "queued": "info",
        "accepted": "info",
        "uncertain": "danger",
        "attention": "danger",
        "retry_budget": "danger",
        "progressed": "success",
        "superseded": "neutral",
        "cancelled": "neutral",
        "auto_running": "accent",
        "auto_watched": "accent",
    }

    def __init__(self, theme="light", parent=None):
        super().__init__(parent)
        self.theme = theme

    def paint(self, painter, option, index):
        values = ui_theme.palette(self.theme)
        paint_row_background(painter, option, self.theme)
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        code = str(index.data(Qt.ItemDataRole.UserRole + 1) or "")
        tone = self.TONES.get(code, "neutral")
        dot = _color(values, "neutral" if tone == "neutral" else tone)
        font = QFont(option.font)
        font.setPixelSize(12)
        painter.save()
        painter.setClipRect(option.rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot)
        painter.drawEllipse(QRectF(option.rect.x() + 13, option.rect.y() + option.rect.height() / 2 - 3, 6, 6))
        painter.setFont(font)
        painter.setPen(QColor(values["text"]))
        metrics = QFontMetrics(font)
        text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, max(10, option.rect.width() - 34))
        painter.drawText(option.rect.x() + 27,
                         option.rect.y() + (option.rect.height() + metrics.ascent() - metrics.descent()) // 2,
                         text)
        painter.restore()
