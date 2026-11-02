"""Reusable widgets used by the redesigned desktop interface."""

from PySide6.QtCore import (Property, QEasingCurve, QPropertyAnimation, QRectF, QSize,
                            QTimer, Qt)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QAbstractButton, QButtonGroup, QComboBox, QFrame,
                               QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                               QProgressBar, QPushButton, QStyle, QTableWidget,
                               QVBoxLayout, QWidget)

from . import theme as ui_theme


def repolish(widget):
    ui_theme.repolish(widget)


def paint_row_background(painter, option, theme):
    values = ui_theme.palette(theme)
    if option.state & QStyle.StateFlag.State_Selected:
        painter.fillRect(option.rect, QColor(values["selection"]))
    elif option.state & QStyle.StateFlag.State_MouseOver:
        painter.fillRect(option.rect, QColor(values["surfaceAlt"]))
    else:
        painter.fillRect(option.rect, QColor(values["surface"]))


class Card(QFrame):
    """White surface with a consistent border and inner rhythm."""

    def __init__(self, parent=None, margins=(20, 18, 20, 18), spacing=14):
        super().__init__(parent)
        self.setObjectName("card")
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(*margins)
        self.box.setSpacing(spacing)


class DataTable(QTableWidget):
    """Table that paints subtle row separators across the full viewport."""

    def __init__(self, rows, columns, theme="light", parent=None):
        super().__init__(rows, columns, parent)
        self.theme = theme

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.rowCount():
            return
        painter = QPainter(self.viewport())
        painter.setPen(QPen(QColor(ui_theme.color(self.theme, "border")), 1))
        top = self.viewport().rect().top()
        bottom = self.viewport().rect().bottom()
        width = self.viewport().width()
        first = max(0, self.rowAt(top))
        last = self.rowAt(bottom)
        if last < 0:
            last = self.rowCount() - 1
        for row in range(first, min(self.rowCount(), last + 1)):
            y = self.rowViewportPosition(row) + self.rowHeight(row) - 1
            if top <= y <= bottom:
                painter.drawLine(0, y, width, y)
        painter.end()


class SectionHeader(QWidget):
    def __init__(self, title, subtitle=None, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        column = QVBoxLayout()
        column.setSpacing(2)
        self.title = QLabel(title)
        self.title.setObjectName("section")
        column.addWidget(self.title)
        self.subtitle = QLabel(subtitle or "")
        self.subtitle.setObjectName("caption")
        self.subtitle.setVisible(bool(subtitle))
        column.addWidget(self.subtitle)
        row.addLayout(column)
        row.addStretch()
        self.row = row

    def add_right(self, widget):
        self.row.addWidget(widget)


class StatusPill(QLabel):
    def __init__(self, text="", state="neutral", parent=None):
        super().__init__(text, parent)
        self.setObjectName("pill")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_state(text, state)

    def set_state(self, text, state):
        self.setText(text)
        self.setProperty("state", state)
        repolish(self)


class AgentSwitcher(QWidget):
    """Segmented control backed by a hidden combo box for stable programmatic use."""

    def __init__(self, items, current="codex", parent=None):
        super().__init__(parent)
        self.combo = QComboBox(self)
        for key, label in items:
            self.combo.addItem(label, key)
        self.combo.hide()
        index = max(0, self.combo.findData(current))
        self.combo.setCurrentIndex(index)
        self.currentIndexChanged = self.combo.currentIndexChanged

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        frame = QFrame()
        frame.setObjectName("inset")
        frame.setStyleSheet("QFrame#inset { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); }")
        segment = QHBoxLayout(frame)
        segment.setContentsMargins(3, 3, 3, 3)
        segment.setSpacing(2)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.names = [label for _, label in items]
        self.buttons = []
        for i, label in enumerate(self.names):
            button = QPushButton(label)
            button.setObjectName("agentSegment")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, index=i: self.setCurrentIndex(index))
            self.group.addButton(button, i)
            segment.addWidget(button)
            self.buttons.append(button)
        outer.addWidget(frame)
        self.combo.currentIndexChanged.connect(self._sync)
        self._sync()

    def _sync(self):
        index = self.combo.currentIndex()
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)

    def setCurrentIndex(self, index):
        self.combo.setCurrentIndex(index)

    def currentIndex(self):
        return self.combo.currentIndex()

    def currentData(self):
        return self.combo.currentData()


class EmptyState(QWidget):
    def __init__(self, icon_name="bulb", parent=None):
        super().__init__(parent)
        self._compact = None
        self._has_action = False
        layout = QVBoxLayout(self)
        self.box = layout
        layout.setContentsMargins(24, 28, 24, 28)
        layout.setSpacing(8)
        layout.addStretch()
        self.icon = QLabel()
        self.icon.setObjectName("emptyIcon")
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_name = icon_name
        layout.addWidget(self.icon)
        self.title = QLabel()
        self.title.setObjectName("emptyTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)
        self.body = QLabel()
        self.body.setObjectName("emptyBody")
        self.body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.body.setWordWrap(False)
        layout.addWidget(self.body, 0, Qt.AlignmentFlag.AlignHCenter)
        self.action = QPushButton()
        self.action.setObjectName("ghost")
        self.action.setVisible(False)
        self._callback = None
        self.action.clicked.connect(self._invoke)
        layout.addWidget(self.action, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_compact()

    def _update_compact(self, force=False):
        compact = self.height() < 190
        if not force and compact == self._compact:
            return
        self._compact = compact
        self.icon.setVisible(not compact)
        self.body.setVisible(not compact)
        self.box.setContentsMargins(24, 10 if compact else 28, 24, 10 if compact else 28)
        self.action.setVisible(self._has_action)

    def _invoke(self):
        if self._callback:
            self._callback()

    def set_content(self, title, body, theme="light", action=None, icon_name=None):
        self.title.setText(title)
        self.body.setText(body)
        name = icon_name or self.icon_name
        self.icon.setPixmap(ui_theme.icon(name, theme, size=30).pixmap(30, 30))
        if action:
            label, callback = action
            self.action.setText(label)
            self._callback = callback
            self._has_action = True
        else:
            self._callback = None
            self._has_action = False
        self._update_compact(force=True)


class AnimatedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self._animation = QPropertyAnimation(self, b"value", self)
        self._animation.setDuration(360)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def setValue(self, value):
        target = max(self.minimum(), min(self.maximum(), int(value)))
        if not self.isVisible():
            super().setValue(target)
            return
        self._animation.stop()
        self._animation.setStartValue(self.value())
        self._animation.setEndValue(target)
        self._animation.start()

    def set_severity(self, severity):
        self.setProperty("severity", severity)
        repolish(self)


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(38, 22)
        self._position = 0.0
        self._animation = QPropertyAnimation(self, b"position", self)
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def _get_position(self):
        return self._position

    def _set_position(self, value):
        self._position = value
        self.update()

    position = Property(float, _get_position, _set_position)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def setChecked(self, checked):
        super().setChecked(checked)
        if not self.isVisible():
            self._position = 1.0 if checked else 0.0
            self.update()

    def sizeHint(self):
        return QSize(38, 22)

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, event):
        values = ui_theme.palette(getattr(self, "theme", "light"))
        theme = getattr(self, "theme", "light")
        if self.isChecked():
            track = QColor(ui_theme.color(theme, "accent"))
        else:
            track = QColor(ui_theme.color(theme, "controlBorder"))
        if not self.isEnabled():
            track = QColor(ui_theme.color(theme, "surfaceSunken"))
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track)
        painter.drawRoundedRect(QRectF(1, 2, 36, 18), 9, 9)
        knob = 14
        x = 3 + (38 - 2 - knob - 4) * max(0.0, min(1.0, self._position))
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(x, 4, knob, knob))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(ui_theme.color(theme, "text")), 1))
            painter.drawRoundedRect(QRectF(0.5, 1.5, 37, 19), 9.5, 9.5)
        painter.end()


class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)
        self.animation = QPropertyAnimation(self.effect, b"opacity", self)
        self.animation.setDuration(180)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.dismiss)
        self.hide()

    def message(self, text, duration=2200):
        self.setText(text)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self.animation.stop()
        self.animation.setStartValue(self.effect.opacity())
        self.animation.setEndValue(1.0)
        self.animation.start()
        self.timer.start(duration)

    def dismiss(self):
        self.animation.stop()
        self.animation.setStartValue(self.effect.opacity())
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self._hide_after)
        self.animation.start()

    def _hide_after(self):
        try:
            self.animation.finished.disconnect(self._hide_after)
        except (RuntimeError, TypeError):
            pass
        if self.effect.opacity() <= 0.01:
            self.hide()

    def reposition(self):
        parent = self.parentWidget()
        if not parent:
            return
        self.move(max(16, (parent.width() - self.width()) // 2), parent.height() - self.height() - 26)
