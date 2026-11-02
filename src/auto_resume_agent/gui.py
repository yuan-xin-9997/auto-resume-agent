import queue
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QByteArray, QEasingCurve, QPropertyAnimation, QSize, Qt, QTimer
from PySide6.QtGui import QFontDatabase, QIcon, QKeySequence
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QCheckBox,
                               QComboBox, QFrame, QGraphicsOpacityEffect,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
                               QStackedWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from .model import wait_for_check
from .engine import Engine
from .i18n import LANGUAGES, tr, duration_label
from .protocol import Codex, BackendError, compatibility_code
from .store import Store
from .backends import create_backend, selected_store, configuration
from . import __version__
from . import window_keeper
from .ui import theme as ui_theme
from .ui.delegates import EventDelegate, ProjectDelegate, SessionDelegate, StatusDelegate
from .ui.widgets import (AgentSwitcher, AnimatedProgressBar, Card, DataTable, EmptyState,
                         SectionHeader, StatusPill, Toast, ToggleSwitch)

ASSETS = Path(__file__).parent / "assets"
STYLE = ui_theme.STYLE


def timestamp(value):
    return time.strftime("%m-%d %H:%M:%S", time.localtime(value)) if value else "—"


class Worker:
    def __init__(self, store):
        self.store = store
        self.inbox, self.outbox = queue.Queue(), queue.Queue()
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def request(self, kind, value=None):
        self.inbox.put((kind, value))
        self.wake.set()

    def run(self):
        backend, engine, configured = None, None, None
        while not self.stop.is_set():
            wait = 5
            try:
                config = configuration(self.store)
                if backend is None or config != configured:
                    if backend:
                        backend.close()
                    backend = create_backend(self.store, config[0])
                    engine = Engine(selected_store(self.store, config[0]), backend)
                    configured = config
                    self.inbox.put(("threads", None))
                while not self.inbox.empty():
                    kind, value = self.inbox.get_nowait()
                    if kind == "threads":
                        self.outbox.put((configured, "threads", (backend.threads(value), value is not None)))
                    elif kind == "refresh":
                        engine.last_usage = 0
                result = engine.tick()
                self.store.set("last_error", None)
                wait = result["delay"]
                self.outbox.put((configured, "tick", result))
            except Exception as error:
                code = str(error) if isinstance(error, BackendError) else "generic_error"
                self.store.set("last_error", code)
                self.outbox.put((configuration(self.store), "error", code))
                if backend:
                    backend.close()
                backend, engine = None, None
                wait = selected_store(self.store, config[0]).interval()
            wait_for_check(self.stop, wait, self.wake)
        if backend:
            backend.close()


class Window(QMainWindow):
    def __init__(self, store, start_worker=True):
        super().__init__()
        self.base_store = store
        self.agent = store.get("agent", "codex")
        self.store = selected_store(store, self.agent)
        self.language = store.get("language", "en")
        self.theme_mode = store.get("theme", "system")
        self.theme = ui_theme.resolve_theme(self.theme_mode)
        self.translated = []
        self.rows = []
        self.checked_ids = set()
        self.cursor = None
        self.latest_tick = {}
        self.loading = False
        self.filter_key = "all"
        self.dirty = False
        self.worker = None
        self._page_animation = None
        self.setWindowTitle("Auto Resume Agent")
        self.setWindowIcon(QIcon(str(ASSETS / "icon.png")))
        self.resize(1200, 800)
        self.setMinimumSize(960, 660)
        self.setStyleSheet(ui_theme.build_stylesheet(self.theme))
        self.build_shell()
        self.build_dashboard()
        self.build_activity()
        self.build_settings()
        self.toast = Toast(self)
        last_page = store.get("last_page", 0)
        self.navigate(last_page if isinstance(last_page, int) and 0 <= last_page < 3 else 0, animate=False)
        geometry = store.get("window_geometry")
        if isinstance(geometry, str) and geometry:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geometry.encode("ascii")))
            except (ValueError, TypeError):
                pass
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(250)
        self.slow_timer = QTimer(self)
        self.slow_timer.timeout.connect(self.render)
        self.slow_timer.start(1000)
        if start_worker:
            self.worker = Worker(self.base_store)
            self.loading = True
        self.apply_theme(refresh=False)
        self.render()

    def text(self, key):
        translated_key = {"help_text": "opencode_help", "hint": "opencode_hint"}.get(key, key) if self.agent == "opencode" else key
        if key == "hint" and self.agent == "codex" and self.base_store.get("auto_watch_quota", True):
            translated_key = "auto_watch_hint"
        value = tr(translated_key, self.language)
        if self.agent == "opencode" and key in ("privacy", "scope", "hint", "about", "thread"):
            value = value.replace("Codex", "OpenCode").replace("UUID", "ID")
        return value.replace("0.1.0", __version__)

    def label(self, key, style=None, wrap=False):
        label = QLabel(self.text(key))
        label.setWordWrap(wrap)
        if style:
            label.setObjectName(style)
        self.translated.append((label, key))
        return label

    def button(self, key, callback):
        button = QPushButton(self.text(key))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(callback)
        self.translated.append((button, key))
        return button

    def icon_button(self, name, tooltip_key, callback):
        button = QPushButton()
        button.setObjectName("icon")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedSize(34, 34)
        button.setIconSize(QSize(17, 17))
        button.clicked.connect(callback)
        self.icon_buttons = getattr(self, "icon_buttons", [])
        self.icon_buttons.append((button, name, tooltip_key))
        button.setToolTip(self.text(tooltip_key))
        button.setAccessibleName(self.text(tooltip_key))
        return button

    def page(self, scroll=False, max_width=None):
        page = QWidget()
        page.setObjectName("page")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(0)
        if max_width:
            column = QWidget()
            column.setMaximumWidth(max_width)
            column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            box = QVBoxLayout(column)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(18)
            outer.addWidget(column, 1, Qt.AlignmentFlag.AlignHCenter)
        else:
            box = outer
            box.setSpacing(18)
        if scroll:
            area = QScrollArea()
            area.setWidgetResizable(True)
            area.setFrameShape(QFrame.Shape.NoFrame)
            area.setWidget(page)
            self.pages.addWidget(area)
        else:
            self.pages.addWidget(page)
        return box

    def build_shell(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(236)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 24, 18, 18)
        side.setSpacing(0)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(QIcon(str(ASSETS / "icon.png")).pixmap(36, 36))
        brand_row.addWidget(logo)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand = QLabel("Auto Resume Agent")
        brand.setObjectName("brand")
        brand_text.addWidget(brand)
        brand_sub = QLabel("RECOVERY MONITOR")
        brand_sub.setObjectName("brandSub")
        brand_text.addWidget(brand_sub)
        brand_row.addLayout(brand_text)
        brand_row.addStretch()
        side.addLayout(brand_row)
        side.addSpacing(26)

        caption = QLabel("AGENT")
        caption.setObjectName("sideCaption")
        side.addWidget(caption)
        side.addSpacing(7)
        self.agents = AgentSwitcher([("codex", "Codex"), ("opencode", "OpenCode")], self.agent)
        self.agents.currentIndexChanged.connect(self.change_agent)
        side.addWidget(self.agents)
        side.addSpacing(26)

        self.pages = QStackedWidget()
        self.navs = []
        nav_box = QVBoxLayout()
        nav_box.setSpacing(2)
        for index, (key, icon_name, shortcut) in enumerate((
                ("dashboard", "dashboard", "Ctrl+1"),
                ("activity", "activity", "Ctrl+2"),
                ("settings", "settings", "Ctrl+3"))):
            button = self.button(key, lambda checked=False, i=index: self.navigate(i))
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setIconSize(QSize(18, 18))
            button.setShortcut(QKeySequence(shortcut))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setAccessibleName(self.text(key))
            nav_box.addWidget(button)
            self.navs.append(button)
        side.addLayout(nav_box)
        side.addStretch()

        status_frame = QFrame()
        status_frame.setObjectName("sideStatus")
        status_box = QVBoxLayout(status_frame)
        status_box.setContentsMargins(10, 9, 10, 9)
        status_box.setSpacing(4)
        status_top = QHBoxLayout()
        status_top.setSpacing(7)
        self.side_dot = QLabel()
        self.side_dot.setFixedSize(8, 8)
        status_top.addWidget(self.side_dot)
        self.side_status = QLabel(self.text("unknown"))
        self.side_status.setObjectName("brandSub")
        self.side_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        status_top.addWidget(self.side_status, 1)
        status_box.addLayout(status_top)
        self.side_detail = QLabel("")
        self.side_detail.setObjectName("brandSub")
        status_box.addWidget(self.side_detail)
        side.addWidget(status_frame)
        side.addSpacing(12)
        version = QLabel("v" + __version__)
        version.setObjectName("brandSub")
        side.addWidget(version)

        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)

    def _set_dot(self, label, tone):
        colors = {"ok": "success", "warning": "warning", "error": "danger",
                  "neutral": "neutral", "accent": "accent"}
        color = ui_theme.color(self.theme, colors.get(tone, "neutral"))
        label.setStyleSheet("background: %s; border-radius: 4px;" % color)

    def _set_connection(self, text, tone="neutral", detail=None):
        self.connection_tone = tone
        self.connection.setText(text)
        tooltip = text + ("\n" + detail if detail else "")
        self.connection.setToolTip(tooltip)
        self.banner.setProperty("tone", "error" if tone == "error" else "warning" if tone == "warning" else "info")
        ui_theme.repolish(self.banner)
        self._set_dot(self.connection_dot, tone)
        status_text = self.text("monitoring" if self.store.get("enabled", False) else "paused")
        self._elide_status()
        self.side_status.setToolTip(tooltip)
        self._set_dot(self.side_dot, tone)
        self.side_detail.setText(self.agent_name() + " · " + status_text)

    def _elide_status(self):
        if not hasattr(self, "connection"):
            return
        full = self.connection.text()
        width = max(40, self.side_status.width())
        self.side_status.setText(self.side_status.fontMetrics().elidedText(full, Qt.TextElideMode.ElideRight, width))

    def agent_name(self):
        return "OpenCode" if self.agent == "opencode" else "Codex"

    def build_dashboard(self):
        box = self.page()
        header = QHBoxLayout()
        header.setSpacing(8)
        titles = QVBoxLayout()
        titles.setSpacing(3)
        self.dashboard_title = self.label("dashboard", "pageTitle")
        self.dashboard_subtitle = self.label("subtitle", "pageSubtitle")
        titles.addWidget(self.dashboard_title)
        titles.addWidget(self.dashboard_subtitle)
        header.addLayout(titles)
        header.addStretch()
        self.badge = StatusPill(self.text("paused"), "neutral")
        header.addWidget(self.badge)
        self.help_button = self.icon_button("help", "help", self.help)
        self.refresh_button = self.icon_button("refresh", "refresh", self.refresh)
        header.addWidget(self.help_button)
        header.addWidget(self.refresh_button)
        self.toggle = QPushButton(self.text("start"))
        self.toggle.setObjectName("primary")
        self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle.setIconSize(QSize(15, 15))
        self.toggle.setMinimumWidth(132)
        self.toggle.clicked.connect(self.toggle_enabled)
        header.addWidget(self.toggle)
        box.addLayout(header)

        self.banner = QFrame()
        self.banner.setObjectName("banner")
        self.banner.setProperty("tone", "info")
        banner_box = QHBoxLayout(self.banner)
        banner_box.setContentsMargins(12, 8, 12, 8)
        banner_box.setSpacing(8)
        self.connection_dot = QLabel()
        self.connection_dot.setFixedSize(8, 8)
        banner_box.addWidget(self.connection_dot)
        self.connection = QLabel(self.text("unknown"))
        self.connection.setObjectName("muted")
        self.connection.setWordWrap(True)
        banner_box.addWidget(self.connection, 1)
        self.last_checked = QLabel("")
        self.last_checked.setObjectName("caption")
        banner_box.addWidget(self.last_checked)
        box.addWidget(self.banner)

        self._set_connection(self.text("unknown"), "neutral")

        self.quota_header = SectionHeader(self.text("quota"))
        self.translated.append((self.quota_header.title, "quota"))
        box.addWidget(self.quota_header)
        self.quota_layout = QHBoxLayout()
        self.quota_layout.setSpacing(16)
        box.addLayout(self.quota_layout)

        card = Card(margins=(20, 16, 20, 12), spacing=12)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.sessions_header = self.label("sessions", "section")
        self.session_count = QLabel("")
        self.session_count.setObjectName("caption")
        head.addWidget(self.sessions_header)
        head.addWidget(self.session_count)
        head.addStretch()
        self.select_all = QCheckBox(self.text("select_all"))
        self.translated.append((self.select_all, "select_all"))
        self.select_all.toggled.connect(self.check_all)
        head.addWidget(self.select_all)
        self.watch_button = self.button("watch", self.watch_selected)
        self.unwatch_button = self.button("unwatch", self.unwatch_selected)
        self.unwatch_button.setObjectName("ghost")
        head.addWidget(self.watch_button)
        head.addWidget(self.unwatch_button)
        card.box.addLayout(head)

        self.session_hint = self.label("hint", "muted", wrap=True)
        card.box.addWidget(self.session_hint)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setAccessibleName(self.text("search_sessions"))
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumWidth(200)
        self.search.setMaximumWidth(340)
        self.search.setMinimumHeight(36)
        self.search.addAction(ui_theme.icon("search", self.theme, size=15), QLineEdit.ActionPosition.LeadingPosition)
        self.search.textChanged.connect(self.render)
        toolbar.addWidget(self.search, 1)
        filter_frame = QFrame()
        filter_frame.setObjectName("inset")
        filter_box = QHBoxLayout(filter_frame)
        filter_box.setContentsMargins(3, 3, 3, 3)
        filter_box.setSpacing(2)
        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        self.filter_buttons = {}
        for key in ("all", "filter_watching", "filter_pending", "filter_attention"):
            button = self.button(key, lambda checked=False, k=key: self.set_filter(k))
            button.setObjectName("segment")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setAccessibleName(self.text(key))
            self.filter_group.addButton(button)
            filter_box.addWidget(button)
            self.filter_buttons[key] = button
        self.filter_buttons["all"].setChecked(True)
        toolbar.addWidget(filter_frame)
        toolbar.addStretch()
        card.box.addLayout(toolbar)

        self.table = self.make_table(4, 56)
        self.table.setAccessibleName(self.text("sessions"))
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 62)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(2, 176)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 162)
        self.table.itemChanged.connect(self.selection_changed)
        self.table.setItemDelegateForColumn(1, SessionDelegate(self.theme, self.table))
        self.table.setItemDelegateForColumn(2, ProjectDelegate(self.theme, self.table))
        self.table.setItemDelegateForColumn(3, StatusDelegate(self.theme, self.table))
        self.table_empty = EmptyState("activity")
        self.table_stack = QStackedWidget()
        self.table_stack.addWidget(self.table)
        self.table_stack.addWidget(self.table_empty)
        card.box.addWidget(self.table_stack, 1)

        footer = QHBoxLayout()
        footer.setSpacing(8)
        self.scope = self.label("scope", "caption")
        footer.addWidget(self.scope)
        footer.addStretch()
        self.more = self.button("more", self.load_more)
        self.more.setObjectName("ghost")
        footer.addWidget(self.more)
        card.box.addLayout(footer)
        box.addWidget(card, 1)

    def make_table(self, columns, row_height=56):
        table = DataTable(0, columns, theme=self.theme)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        table.setMouseTracking(True)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(row_height)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.horizontalHeader().setHighlightSections(False)
        table.horizontalHeader().setSectionsClickable(False)
        table.horizontalHeader().setFixedHeight(38)
        table.setShowGrid(False)
        table.setWordWrap(False)
        table.setAlternatingRowColors(False)
        table.setCornerButtonEnabled(False)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return table

    def build_activity(self):
        box = self.page()
        title = self.label("activity", "pageTitle")
        box.addWidget(title)
        box.addWidget(self.label("privacy", "pageSubtitle"))

        card = Card(margins=(20, 16, 20, 12), spacing=12)
        head = QHBoxLayout()
        head.setSpacing(10)
        self.activity_header = self.label("activity", "section")
        self.activity_count = QLabel("")
        self.activity_count.setObjectName("caption")
        head.addWidget(self.activity_header)
        head.addWidget(self.activity_count)
        head.addStretch()
        self.activity_refresh = self.icon_button("refresh", "refresh", self.refresh)
        head.addWidget(self.activity_refresh)
        card.box.addLayout(head)

        self.events = self.make_table(3, 48)
        self.events.setAccessibleName(self.text("activity"))
        self.events.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.events.setColumnWidth(0, 150)
        self.events.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.events.setColumnWidth(1, 300)
        self.events.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.events.setItemDelegateForColumn(1, SessionDelegate(self.theme, self.events))
        self.events.setItemDelegateForColumn(2, EventDelegate(self.theme, self.events))
        self.events_empty = EmptyState("activity")
        self.events_stack = QStackedWidget()
        self.events_stack.addWidget(self.events)
        self.events_stack.addWidget(self.events_empty)
        card.box.addWidget(self.events_stack, 1)
        box.addWidget(card, 1)

    def _labeled_field(self, key, widget, hint_key=None):
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(5)
        title = QLabel(self.text(key))
        title.setObjectName("cardTitle")
        self.translated.append((title, key))
        column.addWidget(title)
        widget.setAccessibleName(self.text(key))
        if hint_key:
            hint = QLabel(self.text(hint_key))
            hint.setObjectName("caption")
            hint.setWordWrap(True)
            self.translated.append((hint, hint_key))
            column.addWidget(hint)
        column.addWidget(widget)
        return holder

    def _switch_row(self, title_key, detail_key, switch):
        frame = QFrame()
        frame.setObjectName("inset")
        row = QHBoxLayout(frame)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(14)
        text = QVBoxLayout()
        text.setSpacing(3)
        title = QLabel(self.text(title_key))
        title.setObjectName("cardTitle")
        self.translated.append((title, title_key))
        text.addWidget(title)
        detail = QLabel(self.text(detail_key))
        detail.setObjectName("caption")
        detail.setWordWrap(True)
        self.translated.append((detail, detail_key))
        text.addWidget(detail)
        row.addLayout(text, 1)
        switch.theme = self.theme
        row.addWidget(switch, 0, Qt.AlignmentFlag.AlignVCenter)
        return frame

    def build_settings(self):
        container = QWidget()
        container.setObjectName("page")
        outer = QVBoxLayout(container)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("page")
        content_outer = QVBoxLayout(content)
        content_outer.setContentsMargins(32, 28, 32, 26)
        content_outer.setSpacing(0)
        column = QWidget()
        column.setMaximumWidth(820)
        column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        box = QVBoxLayout(column)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(18)
        content_outer.addWidget(column, 1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        self.settings_scroll = scroll
        self.settings_column = column
        self.settings_outer = content_outer

        header = QVBoxLayout()
        header.setSpacing(3)
        header.addWidget(self.label("settings", "pageTitle"))
        header.addWidget(self.label("save_hint", "pageSubtitle"))
        box.addLayout(header)

        general = Card()
        general_header = SectionHeader(self.text("general"))
        self.translated.append((general_header.title, "general"))
        general.box.addWidget(general_header)
        fields = QHBoxLayout()
        fields.setSpacing(16)
        self.themes = QComboBox()
        for key, data in (("theme_system", "system"), ("theme_light", "light"), ("theme_dark", "dark")):
            self.themes.addItem(self.text(key), data)
        self.themes.setCurrentIndex(max(0, self.themes.findData(self.theme_mode)))
        self.themes.currentIndexChanged.connect(self.change_theme)
        self.languages = QComboBox()
        for key, name in LANGUAGES.items():
            self.languages.addItem(name, key)
        self.languages.setCurrentIndex(max(0, self.languages.findData(self.language)))
        self.languages.currentIndexChanged.connect(self.change_language)
        fields.addWidget(self._labeled_field("theme", self.themes), 1)
        fields.addWidget(self._labeled_field("language", self.languages), 1)
        general.box.addLayout(fields)

        intervals = QHBoxLayout()
        intervals.setSpacing(16)
        self.intervals = {}
        for agent in ("codex", "opencode"):
            field = QSpinBox()
            field.setRange(5, 3600)
            field.setSuffix(" s")
            field.setMaximumWidth(180)
            field.setValue(self.base_store.get(agent + "_interval", 30))
            field.valueChanged.connect(lambda value, a=agent: self.change_interval(a, value))
            self.intervals[agent] = field
            intervals.addWidget(self._labeled_field(agent + "_interval_label", field), 1)
        general.box.addLayout(intervals)
        general.box.addWidget(self.label("interval_hint", "caption"))

        self.auto_watch = ToggleSwitch()
        self.auto_watch.theme = self.theme
        self.auto_watch.setChecked(self.base_store.get("auto_watch_quota", True))
        self.auto_watch.toggled.connect(self.toggle_auto_watch)
        self.auto_watch.setAccessibleName(self.text("auto_watch_title"))
        self.auto_watch.setToolTip(self.text("auto_watch_desc"))
        general.box.addWidget(self._switch_row("auto_watch_title", "auto_watch_desc", self.auto_watch))
        box.addWidget(general)

        codex = Card()
        codex_header = SectionHeader(self.text("codex_section"))
        self.translated.append((codex_header.title, "codex_section"))
        codex.box.addWidget(codex_header)
        self.executable = QLineEdit(self.base_store.get("codex_path", ""))
        self.executable.textChanged.connect(self.mark_dirty)
        codex.box.addWidget(self._labeled_field("codex_path_label", self.executable, "codex_path_hint"))
        self.codex_proxy = QLineEdit(self.base_store.get("codex_proxy", ""))
        self.codex_proxy.textChanged.connect(self.mark_dirty)
        codex.box.addWidget(self._labeled_field("codex_proxy_label", self.codex_proxy, "codex_proxy_hint"))
        box.addWidget(codex)

        opencode = Card()
        opencode_header = SectionHeader(self.text("opencode_section"))
        self.translated.append((opencode_header.title, "opencode_section"))
        opencode.box.addWidget(opencode_header)
        self.opencode_url = QLineEdit(self.base_store.get("opencode_url", "http://127.0.0.1:4096"))
        self.opencode_url.textChanged.connect(self.mark_dirty)
        opencode.box.addWidget(self._labeled_field("opencode_url_label", self.opencode_url, "opencode_url_hint"))
        self.opencode_directory = QLineEdit(self.base_store.get("opencode_directory", ""))
        self.opencode_directory.textChanged.connect(self.mark_dirty)
        opencode.box.addWidget(self._labeled_field("opencode_directory_label", self.opencode_directory, "opencode_directory_hint"))
        box.addWidget(opencode)

        self.advanced_card = Card()
        advanced_header = SectionHeader(self.text("advanced"))
        self.translated.append((advanced_header.title, "advanced"))
        self.advanced_card.box.addWidget(advanced_header)
        self.keeper_toggle = ToggleSwitch()
        self.keeper_toggle.theme = self.theme
        self.keeper_toggle.toggled.connect(self.toggle_keeper)
        self.keeper_toggle.setAccessibleName(self.text("keeper_title"))
        self.keeper_toggle.setToolTip(self.text("keeper_desc"))
        self.keeper_row = self._switch_row("keeper_title", "keeper_desc", self.keeper_toggle)
        self.advanced_card.box.addWidget(self.keeper_row)
        self.keeper_status = QLabel("")
        self.keeper_status.setObjectName("caption")
        self.keeper_status.setWordWrap(True)
        self.advanced_card.box.addWidget(self.keeper_status)
        box.addWidget(self.advanced_card)

        about = Card()
        about_title = QLabel("Auto Resume Agent")
        about_title.setObjectName("cardTitle")
        about.box.addWidget(about_title)
        about.box.addWidget(self.label("about", "muted", wrap=True))
        about.box.addWidget(self.label("privacy", "muted", wrap=True))
        box.addWidget(about)
        box.addStretch()

        save_bar = QFrame()
        save_bar.setObjectName("saveBar")
        save_row = QHBoxLayout(save_bar)
        save_row.setContentsMargins(32, 10, 32, 10)
        save_row.setSpacing(12)
        self.dirty_label = QLabel("")
        self.dirty_label.setObjectName("caption")
        save_row.addWidget(self.dirty_label)
        save_row.addStretch()
        self.save_button = self.button("save", self.save)
        self.save_button.setObjectName("primary")
        self.save_button.setEnabled(False)
        save_row.addWidget(self.save_button)
        outer.addWidget(save_bar)
        self.pages.addWidget(container)

    def navigate(self, index, animate=True):
        if not 0 <= index < self.pages.count():
            return
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.navs):
            button.setChecked(i == index)
        self.base_store.set("last_page", index)
        if animate and self.isVisible():
            page = self.pages.currentWidget()
            effect = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b"opacity", self)
            animation.setDuration(150)
            animation.setStartValue(0.35)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            def finish():
                page.setGraphicsEffect(None)

            animation.finished.connect(finish)
            self._page_animation = animation
            animation.start()

    def set_filter(self, key):
        self.filter_key = key
        for name, button in self.filter_buttons.items():
            button.setChecked(name == key)
        self.render()

    def change_language(self):
        self.language = self.languages.currentData()
        self.base_store.set("language", self.language)
        for widget, key in self.translated:
            widget.setText(self.text(key))
        for i, key in enumerate(("theme_system", "theme_light", "theme_dark")):
            self.themes.setItemText(i, self.text(key))
        for button, name, key in getattr(self, "icon_buttons", []):
            button.setToolTip(self.text(key))
            button.setAccessibleName(self.text(key))
        for button, key in zip(self.navs, ("dashboard", "activity", "settings")):
            button.setAccessibleName(self.text(key))
        for key, button in self.filter_buttons.items():
            button.setAccessibleName(self.text(key))
        self.search.setAccessibleName(self.text("search_sessions"))
        self.table.setAccessibleName(self.text("sessions"))
        self.events.setAccessibleName(self.text("activity"))
        self.auto_watch.setAccessibleName(self.text("auto_watch_title"))
        self.keeper_toggle.setAccessibleName(self.text("keeper_title"))
        self.auto_watch.setToolTip(self.text("auto_watch_desc"))
        self.keeper_toggle.setToolTip(self.text("keeper_desc"))
        if self.dirty:
            self.dirty_label.setText(self.text("dirty"))
        if getattr(self, "connection_tone", None) == "ok":
            self._set_connection(self.text("ready").replace("Codex", self.agent_name()), "ok")
        elif getattr(self, "connection_tone", None) == "neutral":
            self._set_connection(self.text("unknown"), "neutral")
        self.render()

    def change_theme(self):
        self.theme_mode = self.themes.currentData()
        self.base_store.set("theme", self.theme_mode)
        self.apply_theme()

    def apply_theme(self, refresh=True):
        self.theme = ui_theme.resolve_theme(self.theme_mode)
        self.setStyleSheet(ui_theme.build_stylesheet(self.theme))
        app = QApplication.instance()
        if app:
            app.setStyleSheet(ui_theme.build_stylesheet(self.theme))
        for button, name, key in getattr(self, "icon_buttons", []):
            button.setIcon(ui_theme.icon(name, self.theme, size=17))
        for button, key in zip(getattr(self, "navs", []), ("dashboard", "activity", "settings")):
            button.setIcon(ui_theme.icon(key, self.theme, tint=ui_theme.color(self.theme, "sidebarMuted"), size=18))
        if hasattr(self, "search"):
            actions = self.search.actions()
            if actions:
                actions[0].setIcon(ui_theme.icon("search", self.theme, size=15))
        for switch in ("auto_watch", "keeper_toggle"):
            if hasattr(self, switch):
                getattr(self, switch).theme = self.theme
        if hasattr(self, "table"):
            self.table.theme = self.theme
            self.table.setItemDelegateForColumn(1, SessionDelegate(self.theme, self.table))
            self.table.setItemDelegateForColumn(2, ProjectDelegate(self.theme, self.table))
            self.table.setItemDelegateForColumn(3, StatusDelegate(self.theme, self.table))
        if hasattr(self, "events"):
            self.events.theme = self.theme
            self.events.setItemDelegateForColumn(1, SessionDelegate(self.theme, self.events))
            self.events.setItemDelegateForColumn(2, EventDelegate(self.theme, self.events))
        if hasattr(self, "connection_tone"):
            self._set_dot(self.connection_dot, self.connection_tone)
            self._set_dot(self.side_dot, self.connection_tone)
        if hasattr(self, "banner"):
            ui_theme.repolish(self.banner)
        self.update_toggle_icon()
        if refresh:
            self.render()

    def update_toggle_icon(self):
        enabled = self.store.get("enabled", False)
        tint = ui_theme.color(self.theme, "accentOn")
        self.toggle.setIcon(ui_theme.icon("pause" if enabled else "play", self.theme, tint=tint, size=15))

    def change_interval(self, agent, value):
        self.base_store.set(agent + "_interval", value)
        if self.worker:
            self.worker.request("refresh")

    def toggle_auto_watch(self, checked):
        self.base_store.set("auto_watch_quota", checked)
        self.refresh()
        self.render()

    def mark_dirty(self):
        if self.dirty:
            return
        self.dirty = True
        self.dirty_label.setText(self.text("dirty"))
        self.save_button.setEnabled(True)

    def save(self):
        from .opencode import endpoint
        from .protocol import proxy_url
        try:
            url = endpoint(self.opencode_url.text().strip())
            proxy = proxy_url(self.codex_proxy.text().strip())
        except BackendError as error:
            QMessageBox.warning(self, self.text("error"), self.text(str(error)))
            return
        self.store.set("enabled", False)
        self.base_store.set("codex_path", self.executable.text().strip())
        self.base_store.set("codex_proxy", proxy or "")
        self.base_store.set("opencode_url", url)
        self.base_store.set("opencode_directory", self.opencode_directory.text().strip())
        self.store = selected_store(self.base_store, self.agent)
        self.store.set("enabled", False)
        self.rows, self.cursor = [], None
        self.checked_ids.clear()
        self.dirty = False
        self.dirty_label.clear()
        self.save_button.setEnabled(False)
        self._set_connection(self.text("saved"), "ok")
        self.toast.message(self.text("settings_saved_toast"))
        self.refresh()
        self.render()

    def change_agent(self, *_):
        self.store.set("enabled", False)
        self.agent = self.agents.currentData()
        self.base_store.set("agent", self.agent)
        self.store = selected_store(self.base_store, self.agent)
        self.store.set("enabled", False)
        self.rows, self.cursor = [], None
        self.checked_ids.clear()
        self.filter_key = "all"
        for widget, key in self.translated:
            widget.setText(self.text(key))
        self._set_connection(self.text("unknown"), "neutral")
        self.refresh()
        self.render()

    def help(self):
        QMessageBox.information(self, self.text("help"), self.text("help_text"))

    def refresh(self):
        if self.worker:
            self.loading = True
            self.worker.request("refresh")
            self.worker.request("threads")
            self.render()

    def load_more(self):
        if self.worker and self.cursor:
            self.loading = True
            self.worker.request("threads", self.cursor)
            self.render()

    def visible_rows(self):
        query = self.search.text().strip().casefold()
        rows = [row for row in self.rows if not query or query in " ".join(
            str(row.get(key) or "") for key in ("name", "id", "cwd")).casefold()]
        if self.filter_key == "all":
            return rows
        watched = {r["id"] for r in self.store.watched()}
        records = {r["thread_id"]: r for r in self.store.records()}
        if self.filter_key == "filter_watching":
            return [row for row in rows if row["id"] in watched]
        if self.filter_key == "filter_pending":
            return [row for row in rows if row["id"] in records
                    and records[row["id"]]["state"] in ("waiting", "queued", "sending", "accepted", "uncertain")]
        if self.filter_key == "filter_attention":
            return [row for row in rows if row["id"] in records
                    and records[row["id"]]["state"] in ("attention", "uncertain")]
        return rows

    def selected(self):
        return [row["id"] for row in self.visible_rows() if row["id"] in self.checked_ids]

    def selection_changed(self, item):
        if item is None or item.column() != 0:
            return
        tid = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            self.checked_ids.add(tid)
        else:
            self.checked_ids.discard(tid)
        self.selection_controls()

    def check_all(self, checked):
        visible = {row["id"] for row in self.visible_rows()}
        if checked:
            self.checked_ids.update(visible)
        else:
            self.checked_ids.difference_update(visible)
        self.render()

    def selection_controls(self):
        self.select_all.blockSignals(True)
        visible = {row["id"] for row in self.visible_rows()}
        self.select_all.setChecked(bool(visible) and visible <= self.checked_ids)
        self.select_all.blockSignals(False)
        self.select_all.setEnabled(bool(visible))
        self.watch_button.setEnabled(bool(self.selected()))
        self.unwatch_button.setEnabled(bool(self.selected()))
        self.session_count.setText(str(len(visible)) if visible else "")
        self.session_count.setToolTip(self.text("sessions") if visible else "")

    def watch_selected(self):
        selected = self.selected()
        for tid in selected:
            self.store.watch(tid)
        if self.worker:
            self.worker.request("refresh")
        if selected:
            self.toast.message(self.text("watched_toast"))
        self.render()

    def unwatch_selected(self):
        selected = self.selected()
        for tid in selected:
            self.store.unwatch(tid)
        if selected:
            self.toast.message(self.text("unwatched_toast"))
        self.render()

    def toggle_enabled(self):
        self.store.set("enabled", not self.store.get("enabled", False))
        if self.worker:
            self.worker.request("refresh")
        self.render()

    def toggle_keeper(self, value):
        if self.agent != "codex":
            return
        window_keeper.set_enabled(self.base_store, value)
        if self.worker:
            self.worker.request("refresh")
        self.render()

    def poll(self):
        if not self.worker:
            return
        while not self.worker.outbox.empty():
            config, kind, data = self.worker.outbox.get_nowait()
            if config != configuration(self.base_store):
                continue
            if kind == "threads":
                page, append = data
                self.loading = False
                rows = page.get("data", [])
                # Providers can repeat UUIDs within a page as well as across pages.
                self.rows = list({r["id"]: r for r in ((self.rows if append else []) + rows)}.values())
                self.cursor = page.get("nextCursor")
            elif kind == "tick":
                self.latest_tick = data
                error = data.get("error")
                if error and compatibility_code(error):
                    self._set_connection(self.text("compatibility_error"), "error", error)
                elif error:
                    message = self.text(error)
                    if message == error:
                        message = self.text("generic_error").replace("Codex", self.agent_name())
                    self._set_connection(message, "warning", error)
                else:
                    self._set_connection(self.text("ready").replace("Codex", self.agent_name()), "ok")
            else:
                self.loading = False
                if data in ("codex_missing", "another_monitor"):
                    self._set_connection(self.text(data), "warning")
                elif compatibility_code(data):
                    self._set_connection(self.text("compatibility_error"), "error", data)
                else:
                    self._set_connection(self.text("generic_error").replace("Codex", self.agent_name()),
                                         "error", data)
            self.render()

    def reset_text(self, reset_at):
        if not reset_at:
            return self.text("reset") + " · —"
        remaining = reset_at - time.time()
        if remaining <= 0:
            return self.text("resetting_soon")
        if remaining < 3600:
            amount = f"{max(1, int(remaining // 60))} {self.text('minutes')}"
        elif remaining < 86400:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            amount = f"{hours} {self.text('hours_short')}"
            if minutes:
                amount += f" {minutes} {self.text('minutes')}"
        else:
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            amount = f"{days} {self.text('days_short')}"
            if hours:
                amount += f" {hours} {self.text('hours_short')}"
        return self.text("resets_in").format(time=amount)

    def build_quota_card(self, window, checked_at):
        card = QFrame()
        card.setObjectName("card")
        box = QVBoxLayout(card)
        box.setContentsMargins(18, 14, 18, 14)
        box.setSpacing(9)
        top = QHBoxLayout()
        top.setSpacing(8)
        if window:
            label_text = f'{window["bucket"]} · {duration_label(window.get("minutes"), self.language)}'
            left = max(0, 100 - window["used_percent"])
            used = 100 - left
            severity = "empty" if left <= 0 else "low" if left <= 20 else "ok"
            tone = {"empty": ("danger", "exhausted"), "low": ("warning", "low"), "ok": ("success", "healthy")}[severity]
            pill = StatusPill(self.text(tone[1]), tone[0])
            amount = f"{left:g}%"
            unit = self.text("remaining")
            reset = self.reset_text(window.get("reset_at"))
            detail = self.text("used") + f" {used:g}%"
            card.setToolTip(self.text("reset") + " · " + timestamp(window.get("reset_at")) + "\n"
                            + self.text("last_checked") + " · " + timestamp(checked_at))
        else:
            label_text = self.agent_name()
            left = 0
            severity = "unknown"
            pill = StatusPill(self.text("unknown"), "neutral")
            amount = self.text("unknown")
            unit = ""
            reset = self.text("quota_not_exposed")
            detail = ""
        bucket = QLabel(label_text)
        bucket.setObjectName("cardTitle")
        top.addWidget(bucket)
        top.addStretch()
        top.addWidget(pill)
        box.addLayout(top)

        metric = QHBoxLayout()
        metric.setSpacing(6)
        number = QLabel(amount)
        number.setObjectName("metric")
        metric.addWidget(number)
        if unit:
            unit_label = QLabel(unit)
            unit_label.setObjectName("metricUnit")
            metric.addWidget(unit_label, 0, Qt.AlignmentFlag.AlignBottom)
        metric.addStretch()
        box.addLayout(metric)

        bar = AnimatedProgressBar()
        bar.setObjectName("quotaBar")
        bar.set_severity(severity)
        bar.setValue(int(left))
        box.addWidget(bar)

        meta = QHBoxLayout()
        meta.setSpacing(8)
        reset_label = QLabel(reset)
        reset_label.setObjectName("caption")
        reset_label.setWordWrap(True)
        meta.addWidget(reset_label, 1)
        if detail:
            detail_label = QLabel(detail)
            detail_label.setObjectName("caption")
            meta.addWidget(detail_label, 0, Qt.AlignmentFlag.AlignRight)
        box.addLayout(meta)
        return card

    def render(self):
        self.search.setPlaceholderText(self.text("search_sessions"))
        self.session_hint.setText(self.text("hint"))
        enabled = self.store.get("enabled", False)
        self.badge.set_state(self.text("monitoring" if enabled else "paused"),
                             "success" if enabled else "neutral")
        self.toggle.setText(self.text("pause" if enabled else "start"))
        self.update_toggle_icon()
        self.more.setEnabled(bool(self.cursor))
        self.side_detail.setText(self.agent_name() + " · " + self.text("monitoring" if enabled else "paused"))

        keeper = window_keeper.status(self.base_store)
        is_codex = self.agent == "codex"
        self.keeper_toggle.setVisible(is_codex)
        self.advanced_card.setVisible(is_codex)
        self.keeper_toggle.blockSignals(True)
        self.keeper_toggle.setChecked(keeper["enabled"])
        self.keeper_toggle.blockSignals(False)
        if keeper["enabled"]:
            detail = self.text("keeper_independent")
            current = self.latest_tick.get("window_keeper") or {}
            reason = current.get("reason")
            if reason in ("keeper_waiting_update", "keeper_waiting_quota", "keeper_no_window",
                          "keeper_recovery_first", "keeper_not_exhausted"):
                detail += " · " + self.text(reason)
            elif keeper.get("next_at"):
                detail += " · " + self.text("keeper_next") + " " + timestamp(keeper["next_at"])
            if keeper.get("last_attempt"):
                detail += " · " + self.text("keeper_last") + " " + self.text("keeper_" + keeper["last_attempt"]["state"])
            self.keeper_status.setText(detail)
        else:
            self.keeper_status.setText(self.text("keeper_off"))

        snapshot = self.store.get("usage", {"windows": []})
        windows = snapshot.get("windows") or []
        quota_key = (tuple((w.get("bucket"), w.get("minutes"), w.get("used_percent"), w.get("reset_at"))
                           for w in windows),
                     self.language, self.theme, self.agent, int(time.time() // 60))
        if getattr(self, "quota_key", None) != quota_key:
            self.quota_key = quota_key
            while self.quota_layout.count():
                item = self.quota_layout.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
            for window in windows or [None]:
                self.quota_layout.addWidget(self.build_quota_card(window, snapshot.get("checked_at")), 1)
        checked = snapshot.get("checked_at")
        self.last_checked.setText(self.text("last_checked") + " · " + timestamp(checked))

        watched = {r["id"] for r in self.store.watched()}
        records = self.store.records()
        # Checkbox state follows IDs, never row positions or transient row highlights.
        self.checked_ids.intersection_update(row["id"] for row in self.rows)
        self.store.remember_sessions(self.rows)
        rows = self.visible_rows()
        table_key = (
            tuple((row["id"], row.get("name"), row.get("cwd")) for row in rows),
            tuple((r["thread_id"], r["state"], r.get("due"), r.get("detail"), r["id"]) for r in records),
            frozenset(watched),
            frozenset(self.checked_ids),
            self.language,
            self.theme,
        )
        if getattr(self, "table_key", None) != table_key:
            self.table_key = table_key
            scroll = self.table.verticalScrollBar().value()
            self.table.setHorizontalHeaderLabels([self.text(k) for k in ("select", "thread", "project", "status")])
            self.table.blockSignals(True)
            self.table.setRowCount(len(rows))
            for index, row in enumerate(rows):
                tid = row["id"]
                record = next((r for r in records if r["thread_id"] == tid), None)
                # A cancelled historical recovery must not hide an active watch.
                if tid in watched and record and record["state"] == "cancelled":
                    record = None
                state = record["state"] if record else ("watching" if tid in watched else "unwatched")
                title = row.get("name") or tid
                name = QTableWidgetItem(title + ("\n" + tid if title != tid else ""))
                name.setToolTip(title + "\n" + tid)
                name.setData(Qt.ItemDataRole.UserRole, tid)
                check = QTableWidgetItem()
                check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
                check.setData(Qt.ItemDataRole.UserRole, tid)
                check.setCheckState(Qt.CheckState.Checked if tid in self.checked_ids else Qt.CheckState.Unchecked)
                self.table.setItem(index, 0, check)
                self.table.setItem(index, 1, name)
                folder = str(row.get("cwd") or "")
                project = QTableWidgetItem(Path(folder).name)
                project.setToolTip(folder)
                self.table.setItem(index, 2, project)
                full = self.text(state)
                # Keep the pill compact; the explanation lives in the tooltip.
                status = QTableWidgetItem(full.split(" · ")[0])
                status.setData(Qt.ItemDataRole.UserRole + 1, state)
                if record:
                    tooltip = [full, self.text(record["detail"]), record["id"]]
                    if record["state"] == "waiting":
                        tooltip.insert(2, self.text("reset") + " · " + timestamp(record["due"]))
                    status.setToolTip("\n".join(tooltip))
                self.table.setItem(index, 3, status)
                for cell in (name, project, status):
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.table.blockSignals(False)
            self.table.verticalScrollBar().setValue(scroll)
        self.table_stack.setCurrentWidget(self.table if rows else self.table_empty)
        empty_key = (self.language, self.loading, self.theme, bool(rows), self.filter_key)
        if getattr(self, "table_empty_key", None) != empty_key:
            self.table_empty_key = empty_key
            if self.loading and not self.rows:
                self.table_empty.set_content(self.text("loading_sessions"), "", theme=self.theme,
                                             icon_name="refresh", action=None)
            else:
                self.table_empty.set_content(self.text("no_sessions_title"), self.text("no_sessions_body"),
                                             theme=self.theme, icon_name="dashboard",
                                             action=(self.text("refresh"), self.refresh))
        self.selection_controls()

        events = self.store.events()
        events_key = (tuple((e["id"], e["time"], e["thread_id"], e["code"]) for e in events),
                      self.language, self.theme)
        if getattr(self, "events_table_key", None) != events_key:
            self.events_table_key = events_key
            scroll = self.events.verticalScrollBar().value()
            self.events.setHorizontalHeaderLabels([self.text(k) for k in ("time", "thread", "event")])
            self.events.setRowCount(len(events))
            names = self.store.session_names()
            fixed = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
            fixed.setPointSize(9)
            for index, event in enumerate(events):
                tid = event["thread_id"]
                title = names.get(tid)
                session = title + "\n" + tid if title else tid or "—"
                time_item = QTableWidgetItem(timestamp(event["time"]))
                time_item.setFont(fixed)
                self.events.setItem(index, 0, time_item)
                session_item = QTableWidgetItem(session)
                session_item.setToolTip(session)
                session_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.events.setItem(index, 1, session_item)
                event_item = QTableWidgetItem(self.text(event["code"]))
                event_item.setData(Qt.ItemDataRole.UserRole + 1, event["code"])
                event_item.setToolTip(self.text(event["code"]))
                event_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.events.setItem(index, 2, event_item)
            self.events.verticalScrollBar().setValue(scroll)
        self.activity_count.setText(str(len(events)) if events else "")
        self.activity_count.setToolTip(self.text("event") if events else "")
        self.events_stack.setCurrentWidget(self.events if events else self.events_empty)
        events_key = (self.language, self.theme)
        if getattr(self, "events_empty_key", None) != events_key:
            self.events_empty_key = events_key
            self.events_empty.set_content(self.text("no_activity_title"), self.text("no_activity_body"),
                                          theme=self.theme, icon_name="activity")
        for key, button in self.filter_buttons.items():
            button.setChecked(key == self.filter_key)

    def closeEvent(self, event):
        geometry = bytes(self.saveGeometry().toBase64()).decode("ascii")
        self.base_store.set("window_geometry", geometry)
        self.base_store.set("last_page", self.pages.currentIndex())
        if self.worker:
            self.worker.stop.set()
            self.worker.wake.set()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._elide_status()
        self._center_settings()
        if hasattr(self, "toast"):
            self.toast.reposition()

    def _center_settings(self):
        if not hasattr(self, "settings_scroll"):
            return
        viewport = self.settings_scroll.viewport().width()
        width = max(320, min(820, viewport - 64))
        margin = max(32, (viewport - width) // 2)
        self.settings_outer.setContentsMargins(margin, 28, margin, 26)


def main(store=None):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setStyle("Fusion")
    app.setApplicationName("Auto Resume Agent")
    app.setOrganizationName("AutoResumeAgent")
    smoke = "--smoke-test" in sys.argv
    if smoke:
        import tempfile
        isolated = tempfile.TemporaryDirectory()
        store = Store(isolated.name)
    window = Window(store or Store(), start_worker=not smoke)
    app.setStyleSheet(ui_theme.build_stylesheet(window.theme))
    window.show()
    if smoke:
        def finish_smoke():
            if not window.isVisible():
                app.exit(1)
                return
            window.close()
            app.quit()
        QTimer.singleShot(1500, finish_smoke)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
