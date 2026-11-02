"""Design tokens, icons and the Qt stylesheet."""

from pathlib import Path
from string import Template
import sys

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

ASSETS = Path(__file__).resolve().parent.parent / "assets"

LIGHT = {
    "canvas": "#F6F7F9",
    "surface": "#FFFFFF",
    "surfaceAlt": "#F9FAFB",
    "surfaceSunken": "#F2F4F7",
    "border": "#E4E7EC",
    "borderStrong": "#D0D5DD",
    "controlBorder": "#CFD4DC",
    "text": "#101828",
    "muted": "#667085",
    "disabled": "#98A2B3",
    "accent": "#0F766E",
    "accentHover": "#0D9488",
    "accentOn": "#FFFFFF",
    "accentText": "#0F766E",
    "accentSoft": "#E7F5F2",
    "success": "#15803D",
    "successSoft": "#ECFDF3",
    "warning": "#B54708",
    "warningSoft": "#FFFAEB",
    "danger": "#B42318",
    "dangerSoft": "#FEF3F2",
    "info": "#175CD3",
    "infoSoft": "#EFF8FF",
    "neutral": "#667085",
    "neutralSoft": "#F2F4F7",
    "track": "#EEF0F3",
    "scroll": "#D0D5DD",
    "scrollHover": "#98A2B3",
    "selection": "#E7F5F2",
    "sidebar": "#101828",
    "sidebarText": "#F2F4F7",
    "sidebarMuted": "#98A2B3",
    "sidebarAccent": "#5EEAD4",
    "sidebarLine": "rgba(255,255,255,0.08)",
    "sidebarHover": "rgba(255,255,255,0.06)",
    "inverse": "#101828",
    "inverseText": "#FFFFFF",
    "chevron": "chevron-down-light.svg",
    "chevron_up": "chevron-up-light.svg",
    "check": "check.svg",
}

DARK = {
    "canvas": "#0B1220",
    "surface": "#111827",
    "surfaceAlt": "#172033",
    "surfaceSunken": "#1E293B",
    "border": "#243044",
    "borderStrong": "#334155",
    "controlBorder": "#334155",
    "text": "#E5E7EB",
    "muted": "#98A2B3",
    "disabled": "#64748B",
    "accent": "#2DD4BF",
    "accentHover": "#5EEAD4",
    "accentOn": "#062C27",
    "accentText": "#5EEAD4",
    "accentSoft": "rgba(45,212,191,0.14)",
    "success": "#4ADE80",
    "successSoft": "rgba(74,222,128,0.12)",
    "warning": "#FBBF24",
    "warningSoft": "rgba(251,191,36,0.12)",
    "danger": "#F87171",
    "dangerSoft": "rgba(248,113,113,0.12)",
    "info": "#60A5FA",
    "infoSoft": "rgba(96,165,250,0.12)",
    "neutral": "#94A3B8",
    "neutralSoft": "rgba(148,163,184,0.12)",
    "track": "#243044",
    "scroll": "#334155",
    "scrollHover": "#475569",
    "selection": "rgba(45,212,191,0.14)",
    "sidebar": "#080F1C",
    "sidebarText": "#F2F4F7",
    "sidebarMuted": "#8CA0B3",
    "sidebarAccent": "#5EEAD4",
    "sidebarLine": "rgba(255,255,255,0.07)",
    "sidebarHover": "rgba(255,255,255,0.05)",
    "inverse": "#E5E7EB",
    "inverseText": "#0B1220",
    "chevron": "chevron-down-dark.svg",
    "chevron_up": "chevron-up-dark.svg",
    "check": "check.svg",
}

PALETTES = {"light": LIGHT, "dark": DARK}

STATE_COLORS = {
    "success": ("success", "successSoft"),
    "warning": ("warning", "warningSoft"),
    "danger": ("danger", "dangerSoft"),
    "info": ("info", "infoSoft"),
    "neutral": ("neutral", "neutralSoft"),
    "accent": ("accentText", "accentSoft"),
}

FONT_STACK = {
    "win32": '"Microsoft YaHei UI", "Segoe UI Variable Text", "Segoe UI"',
    "darwin": '"PingFang SC", "SF Pro Text", "Helvetica Neue"',
}.get(sys.platform, '"Noto Sans CJK SC", "Noto Sans", "DejaVu Sans"')


def current_theme():
    """Return the effective theme, following the operating system by default."""
    hints = QGuiApplication.styleHints()
    scheme = getattr(hints, "colorScheme", lambda: None)()
    return "dark" if scheme == Qt.ColorScheme.Dark else "light"


def resolve_theme(mode):
    return current_theme() if mode not in ("light", "dark") else mode


def palette(name):
    return PALETTES["dark" if name == "dark" else "light"]


def color(name, token):
    return palette(name)[token]


def icon(name, theme="light", tint=None, size=18):
    """Render one of the bundled line icons with a theme-aware tint."""
    values = palette(theme)
    tint = tint or values["muted"]
    path = ASSETS / (name if name.endswith(".svg") else name + ".svg")
    if not path.exists():
        return QIcon()
    renderer = QSvgRenderer(QByteArray(path.read_text(encoding="utf-8")
                                       .replace("#000000", tint).replace("#000", tint).encode("utf-8")))
    scale = 2
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(scale)
    return QIcon(pixmap)


def repolish(widget):
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


STYLE_TEMPLATE = Template("""
* { outline: none; }
QWidget { background: transparent; color: $text; font-family: $font; font-size: 13px; }
QMainWindow, QWidget#root, QWidget#page { background: $canvas; }
QLabel { background: transparent; }

QLabel#pageTitle { font-size: 22px; font-weight: 600; }
QLabel#pageSubtitle { color: $muted; font-size: 13px; }
QLabel#section { font-size: 16px; font-weight: 600; }
QLabel#cardTitle { font-size: 13px; font-weight: 600; }
QLabel#metric { font-size: 30px; font-weight: 700; }
QLabel#metricUnit { font-size: 13px; color: $muted; }
QLabel#caption, QLabel#muted { color: $muted; font-size: 12px; }
QLabel#mono { color: $muted; font-size: 11px; font-family: "Cascadia Mono", "SF Mono", "Consolas", monospace; }
QLabel#brand { color: $sidebarText; font-size: 15px; font-weight: 600; }
QLabel#brandSub { color: $sidebarMuted; font-size: 10px; }
QLabel#sideCaption { color: $sidebarMuted; font-size: 10px; font-weight: 600; }
QLabel#about { color: $muted; font-size: 12px; }

QFrame#card { background: $surface; border: 1px solid $border; border-radius: 10px; }
QFrame#card QLabel { background: transparent; }
QFrame#inset { background: $surfaceAlt; border: 1px solid $border; border-radius: 8px; }
QFrame#separator { background: $border; border: none; max-height: 1px; }
QFrame#sidebar { background: $sidebar; border: none; }
QFrame#sidebar QLabel { color: $sidebarText; }
QFrame#sidebar QLabel#brandSub, QFrame#sidebar QLabel#sideCaption { color: $sidebarMuted; }
QFrame#sideStatus { background: $sidebarHover; border: 1px solid $sidebarLine; border-radius: 8px; }
QFrame#saveBar { background: $surface; border-top: 1px solid $border; }
QFrame#banner { border-radius: 8px; border: 1px solid $border; background: $surface; }
QFrame#banner[tone="error"] { background: $dangerSoft; border-color: transparent; }
QFrame#banner[tone="warning"] { background: $warningSoft; border-color: transparent; }
QFrame#banner[tone="info"] { background: $infoSoft; border-color: transparent; }

QLabel#pill { border-radius: 9px; padding: 4px 10px; font-size: 11px; font-weight: 600; background: $neutralSoft; color: $neutral; }
QLabel#pill[state="success"] { background: $successSoft; color: $success; }
QLabel#pill[state="warning"] { background: $warningSoft; color: $warning; }
QLabel#pill[state="danger"] { background: $dangerSoft; color: $danger; }
QLabel#pill[state="info"] { background: $infoSoft; color: $info; }
QLabel#pill[state="accent"] { background: $accentSoft; color: $accentText; }
QLabel#pill[state="neutral"] { background: $neutralSoft; color: $neutral; }

QPushButton { background: $surface; color: $text; border: 1px solid $border; border-radius: 8px; padding: 8px 14px; min-height: 18px; }
QPushButton:hover { background: $surfaceAlt; border-color: $borderStrong; }
QPushButton:pressed { background: $surfaceSunken; }
QPushButton:focus { border: 1px solid $accent; }
QPushButton:disabled { color: $disabled; background: $surfaceAlt; border-color: $border; }
QPushButton#primary { background: $accent; color: $accentOn; border: 1px solid $accent; font-weight: 600; }
QPushButton#primary:hover { background: $accentHover; border-color: $accentHover; }
QPushButton#primary:pressed { background: $accent; }
QPushButton#primary:disabled { background: $surfaceSunken; border-color: $border; color: $disabled; }
QPushButton#ghost { background: transparent; border: none; color: $muted; padding: 8px 10px; }
QPushButton#ghost:hover { background: $surfaceAlt; color: $text; }
QPushButton#ghost:checked { background: $accentSoft; color: $accentText; }
QPushButton#icon { background: transparent; border: none; padding: 6px; border-radius: 8px; }
QPushButton#icon:hover { background: $surfaceAlt; }
QPushButton#danger { color: $danger; }
QPushButton#danger:hover { background: $dangerSoft; border-color: transparent; }
QPushButton#segment { background: transparent; border: none; color: $muted; padding: 6px 11px; border-radius: 6px; font-size: 12px; }
QPushButton#segment:hover { background: $surfaceSunken; color: $text; }
QPushButton#segment:checked { background: $surface; color: $text; font-weight: 600; }
QPushButton#agentSegment { background: transparent; border: none; color: $sidebarMuted; padding: 7px 6px; border-radius: 6px; font-size: 12px; }
QPushButton#agentSegment:hover { background: $sidebarHover; color: $sidebarText; }
QPushButton#agentSegment:checked { background: rgba(45,212,191,0.16); color: $sidebarAccent; font-weight: 600; }
QPushButton#nav { text-align: left; background: transparent; border: none; color: $sidebarMuted; padding: 9px 12px; border-radius: 8px; font-size: 13px; }
QPushButton#nav:hover { background: $sidebarHover; color: $sidebarText; }
QPushButton#nav:checked { background: rgba(45,212,191,0.13); color: $sidebarText; font-weight: 600; border-left: 3px solid $sidebarAccent; padding-left: 9px; }
QPushButton#nav:focus { border: 1px solid $sidebarAccent; }
QPushButton#link { background: transparent; border: none; color: $accentText; padding: 4px 2px; font-size: 12px; }
QPushButton#link:hover { color: $accentHover; }

QLineEdit, QComboBox, QSpinBox { background: $surface; color: $text; border: 1px solid $controlBorder; border-radius: 8px; padding: 8px 10px; min-height: 20px; selection-background-color: $accent; selection-color: #FFFFFF; }
QLineEdit:hover, QComboBox:hover, QSpinBox:hover { border-color: $borderStrong; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid $accent; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled { color: $disabled; background: $surfaceAlt; }
QLineEdit#search { padding-left: 32px; }
QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: center right; width: 26px; border: none; }
QComboBox::down-arrow { image: url("$assets/$chevron"); width: 12px; height: 12px; }
QSpinBox { padding-right: 28px; }
QSpinBox::up-button, QSpinBox::down-button { subcontrol-origin: border; width: 22px; background: transparent; border: none; }
QSpinBox::up-button { subcontrol-position: top right; }
QSpinBox::down-button { subcontrol-position: bottom right; }
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: $surfaceAlt; }
QSpinBox::up-arrow { image: url("$assets/$chevron_up"); width: 9px; height: 9px; }
QSpinBox::down-arrow { image: url("$assets/$chevron"); width: 9px; height: 9px; }
QComboBox QAbstractItemView { background: $surface; color: $text; border: 1px solid $border; border-radius: 8px; padding: 4px; selection-background-color: $accentSoft; selection-color: $text; outline: none; }
QComboBox QAbstractItemView::item { min-height: 28px; padding: 4px 8px; border-radius: 6px; }

QCheckBox { spacing: 8px; color: $text; }
QCheckBox::indicator, QTableWidget::indicator { width: 16px; height: 16px; border: 1px solid $controlBorder; border-radius: 4px; background: $surface; }
QCheckBox::indicator:hover, QTableWidget::indicator:hover { border-color: $accent; }
QCheckBox::indicator:checked, QTableWidget::indicator:checked { background: $accent; border-color: $accent; image: url("$assets/$check"); }
QCheckBox::indicator:disabled, QTableWidget::indicator:disabled { background: $surfaceSunken; border-color: $border; }

QProgressBar { background: $track; border: none; border-radius: 3px; min-height: 6px; max-height: 6px; }
QProgressBar::chunk { background: $accent; border-radius: 3px; }
QProgressBar#quotaBar[severity="ok"]::chunk { background: $success; }
QProgressBar#quotaBar[severity="low"]::chunk { background: $warning; }
QProgressBar#quotaBar[severity="empty"]::chunk { background: $danger; }
QProgressBar#quotaBar[severity="unknown"]::chunk { background: $neutral; }

QTableWidget { background: $surface; border: none; border-top: 1px solid $border; border-radius: 0; selection-background-color: $selection; selection-color: $text; alternate-background-color: $surfaceAlt; }
QTableWidget::item { padding: 0px 12px; border: none; }
QTableWidget::item:hover { background: $surfaceAlt; }
QTableWidget::item:selected { background: $selection; color: $text; }
QHeaderView::section { background: $surface; color: $muted; border: none; border-bottom: 1px solid $border; padding: 9px 12px; font-size: 11px; font-weight: 600; }
QHeaderView::section:first { padding-left: 12px; }
QTableCornerButton::section { background: $surface; border: none; }
QTableWidget QTableCornerButton::section { background: $surface; }

QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $scroll; min-height: 28px; border-radius: 3px; }
QScrollBar::handle:vertical:hover { background: $scrollHover; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: $scroll; min-width: 28px; border-radius: 3px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }

QToolTip { color: $text; background: $surface; border: 1px solid $border; border-radius: 6px; padding: 6px 8px; }
QMessageBox { background: $surface; }
QMessageBox QLabel { color: $text; }
QMessageBox QPushButton { min-width: 84px; }

QLabel#toast { background: $inverse; color: $inverseText; border-radius: 8px; padding: 10px 16px; font-size: 12px; }
QLabel#emptyIcon { color: $disabled; }
QLabel#emptyTitle { color: $text; font-size: 14px; font-weight: 600; }
QLabel#emptyBody { color: $muted; font-size: 12px; }
""")


def build_stylesheet(theme="light"):
    values = dict(palette(theme))
    values["font"] = FONT_STACK
    values["assets"] = ASSETS.as_posix()
    return STYLE_TEMPLATE.substitute(values)


STYLE = build_stylesheet("light")
