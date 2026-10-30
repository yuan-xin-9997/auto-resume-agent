import os
import queue
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStackedWidget, QFrame, QProgressBar, QMessageBox, QCheckBox)

from .engine import Engine
from .i18n import LANGUAGES, tr, duration_label
from .protocol import Codex, BackendError, compatibility_code
from .store import Store
from .backends import create_backend, selected_store, configuration
from . import __version__
from . import window_keeper

ASSETS = Path(__file__).parent / "assets"

STYLE = """
QWidget { background: #fafafa; color: #18181b; font-family: 'Segoe UI', 'Noto Sans', sans-serif; font-size: 13px; }
QFrame#sidebar { background: #f4f4f5; border-right: 1px solid #e4e4e7; }
QFrame#sidebar QLabel { background: transparent; }
QLabel#brand { font-size: 19px; font-weight: 700; }
QLabel#title { font-size: 26px; font-weight: 700; }
QLabel#muted { color: #71717a; }
QLabel#badge { color: #52525b; background: #f4f4f5; padding: 7px 12px; border-radius: 6px; }
QLabel#section { font-size: 17px; font-weight: 600; }
QFrame#card { background: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; }
QFrame#card QLabel { background: transparent; }
QLabel { background: transparent; }
QScrollBar:vertical { background: #fafafa; width: 10px; }
QScrollBar::handle:vertical { background: #d4d4d8; min-height: 24px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QLabel#amount { font-size: 30px; font-weight: 700; }
QPushButton { background: #ffffff; border: 1px solid #d4d4d8; padding: 10px 16px; border-radius: 7px; }
QPushButton:hover { background: #f4f4f5; }
QPushButton:disabled { color: #a1a1aa; }
QPushButton#primary { background: #27272a; color: #ffffff; border: none; font-weight: 600; }
QPushButton#primary:hover { background: #52525b; }
QPushButton#nav { text-align: left; background: transparent; border: none; padding: 13px; }
QPushButton#nav:checked { background: #e4e4e7; color: #18181b; }
QTableWidget { background: #ffffff; gridline-color: #e4e4e7; border: 1px solid #e4e4e7; border-radius: 8px; selection-background-color: #e4e4e7; }
QTableWidget::item { padding: 12px; }
QHeaderView::section { background: #f4f4f5; color: #52525b; border: none; padding: 12px 3px; }
QCheckBox::indicator, QTableWidget::indicator { width: 16px; height: 16px; border: 1px solid #a1a1aa; border-radius: 3px; background: #ffffff; }
QCheckBox::indicator:hover, QTableWidget::indicator:hover { border-color: #52525b; }
QLineEdit, QComboBox { background: #f4f4f5; border: 1px solid #d4d4d8; border-radius: 6px; padding: 9px; }
QProgressBar { background: #e4e4e7; border: none; border-radius: 4px; max-height: 7px; }
QProgressBar::chunk { background: #71717a; border-radius: 4px; }
QToolTip { color: #18181b; background: #ffffff; border: 1px solid #d4d4d8; }
"""
STYLE = STYLE.replace("'Segoe UI', 'Noto Sans', sans-serif", {
    "win32": "'Microsoft YaHei UI'", "darwin": "'PingFang SC'"}.get(sys.platform, "'Noto Sans CJK SC'"))
STYLE += 'QCheckBox::indicator:checked, QTableWidget::indicator:checked { background: #27272a; border-color: #27272a; image: url("' + (ASSETS / 'check.svg').as_posix() + '"); }'


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
                wait = 10
            self.wake.wait(wait)
            self.wake.clear()
        if backend:
            backend.close()


class Window(QMainWindow):
    def __init__(self, store, start_worker=True):
        super().__init__()
        self.base_store = store
        self.agent = store.get("agent", "codex")
        self.store = selected_store(store, self.agent)
        self.language = store.get("language", "en")
        self.translated = []
        self.rows = []
        self.checked_ids = set()
        self.cursor = None
        self.latest_tick = {}
        self.worker = None
        self.setWindowTitle("Auto Resume Agent")
        self.setWindowIcon(QIcon(str(ASSETS / "icon.png")))
        self.resize(1200, 800)
        self.setMinimumSize(940, 650)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 28, 18, 24)
        logo = QLabel()
        logo.setPixmap(QIcon(str(ASSETS / "icon.png")).pixmap(52, 52))
        side.addWidget(logo)
        brand = QLabel("Auto Resume\nAgent")
        brand.setObjectName("brand")
        side.addWidget(brand)
        side.addSpacing(30)
        self.pages = QStackedWidget()
        self.navs = []
        for index, key in enumerate(("dashboard", "activity", "settings")):
            button = self.button(key, lambda checked=False, i=index: self.navigate(i))
            button.setObjectName("nav")
            button.setCheckable(True)
            side.addWidget(button)
            self.navs.append(button)
        side.addStretch()
        side.addWidget(self.label("privacy", "muted", wrap=True))
        side.addSpacing(15)
        side.addWidget(QLabel("v" + __version__))
        layout.addWidget(sidebar)
        layout.addWidget(self.pages, 1)
        self.build_dashboard()
        self.build_activity()
        self.build_settings()
        self.navigate(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(250)
        self.slow_timer = QTimer(self)
        self.slow_timer.timeout.connect(self.render)
        self.slow_timer.start(1000)
        if start_worker:
            self.worker = Worker(self.base_store)
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
        button.clicked.connect(callback)
        self.translated.append((button, key))
        return button

    def page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(30, 28, 30, 25)
        box.setSpacing(17)
        self.pages.addWidget(page)
        return box

    def build_dashboard(self):
        box = self.page()
        box.setSpacing(10)
        top = QHBoxLayout()
        top.addWidget(self.label("dashboard", "title"))
        top.addStretch()
        self.badge = QLabel()
        self.badge.setObjectName("badge")
        top.addWidget(self.badge)
        box.addLayout(top)
        box.addWidget(self.label("subtitle", "muted"))
        self.agents = QComboBox()
        self.agents.addItem("Codex", "codex")
        self.agents.addItem("OpenCode", "opencode")
        self.agents.setCurrentIndex(1 if self.agent == "opencode" else 0)
        self.agents.currentIndexChanged.connect(self.change_agent)
        box.addWidget(self.agents)
        self.keeper_toggle = QCheckBox(self.text("keeper_toggle"))
        self.translated.append((self.keeper_toggle, "keeper_toggle"))
        self.keeper_toggle.toggled.connect(self.toggle_keeper)
        box.addWidget(self.keeper_toggle)
        self.keeper_status = QLabel()
        self.keeper_status.setObjectName("muted")
        self.keeper_status.setWordWrap(True)
        box.addWidget(self.keeper_status)
        controls = QHBoxLayout()
        self.toggle = QPushButton()
        self.toggle.setObjectName("primary")
        self.toggle.clicked.connect(self.toggle_enabled)
        controls.addWidget(self.toggle)
        controls.addWidget(self.button("refresh", self.refresh))
        controls.addStretch()
        controls.addWidget(self.button("help", self.help))
        box.addLayout(controls)
        box.addWidget(self.label("quota", "section"))
        self.quota_layout = QHBoxLayout()
        box.addLayout(self.quota_layout)
        self.connection = QLabel(self.text("unknown"))
        self.connection.setObjectName("muted")
        self.connection.setWordWrap(True)
        box.addWidget(self.connection)
        box.addWidget(self.label("sessions", "section"))
        self.session_hint = self.label("hint", "muted", wrap=True)
        box.addWidget(self.session_hint)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.render)
        box.addWidget(self.search)
        buttons = QHBoxLayout()
        self.select_all = QCheckBox(self.text("select_all"))
        self.translated.append((self.select_all, "select_all"))
        self.select_all.toggled.connect(self.check_all)
        buttons.addWidget(self.select_all)
        self.watch_button = self.button("watch", self.watch_selected)
        self.unwatch_button = self.button("unwatch", self.unwatch_selected)
        buttons.addWidget(self.watch_button)
        buttons.addWidget(self.unwatch_button)
        buttons.addStretch()
        self.more = self.button("more", self.load_more)
        buttons.addWidget(self.more)
        box.addLayout(buttons)
        self.table = self.make_table(4)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 70)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(2, 190)
        self.table.setColumnWidth(3, 270)
        self.table.itemChanged.connect(self.selection_changed)
        box.addWidget(self.table, 1)
        box.addWidget(self.label("scope", "muted"))

    def make_table(self, columns):
        table = QTableWidget(0, columns)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.verticalHeader().hide()
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        table.setShowGrid(False)
        table.setWordWrap(False)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setDefaultSectionSize(76)
        return table

    def build_activity(self):
        box = self.page()
        box.addWidget(self.label("activity", "title"))
        box.addWidget(self.label("privacy", "muted"))
        self.events = self.make_table(3)
        self.events.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.events.setColumnWidth(0, 150)
        self.events.setColumnWidth(1, 300)
        box.addWidget(self.events)

    def build_settings(self):
        box = self.page()
        box.addWidget(self.label("settings", "title"))
        box.addWidget(self.label("language", "section"))
        self.languages = QComboBox()
        for key, name in LANGUAGES.items():
            self.languages.addItem(name, key)
        self.languages.setCurrentIndex(max(0, self.languages.findData(self.language)))
        self.languages.currentIndexChanged.connect(self.change_language)
        box.addWidget(self.languages)
        self.auto_watch = QCheckBox(self.text("auto_watch_toggle"))
        self.translated.append((self.auto_watch, "auto_watch_toggle"))
        self.auto_watch.setChecked(self.base_store.get("auto_watch_quota", True))
        self.auto_watch.toggled.connect(self.toggle_auto_watch)
        box.addWidget(self.auto_watch)
        box.addWidget(self.label("codex_path", "section"))
        self.executable = QLineEdit(self.base_store.get("codex_path", ""))
        box.addWidget(self.executable)
        box.addWidget(self.label("codex_proxy", "section"))
        self.codex_proxy = QLineEdit(self.base_store.get("codex_proxy", ""))
        box.addWidget(self.codex_proxy)
        box.addWidget(self.label("opencode_url", "section"))
        self.opencode_url = QLineEdit(self.base_store.get("opencode_url", "http://127.0.0.1:4096"))
        box.addWidget(self.opencode_url)
        box.addWidget(self.label("opencode_directory", "section"))
        self.opencode_directory = QLineEdit(self.base_store.get("opencode_directory", ""))
        box.addWidget(self.opencode_directory)
        box.addWidget(self.button("save", self.save))
        box.addWidget(self.label("confirm_close", "muted", wrap=True))
        box.addStretch()
        box.addWidget(self.label("about", "muted"))

    def navigate(self, index):
        self.pages.setCurrentIndex(index)
        for i, button in enumerate(self.navs):
            button.setChecked(i == index)

    def change_language(self):
        self.language = self.languages.currentData()
        self.base_store.set("language", self.language)
        for widget, key in self.translated:
            widget.setText(self.text(key))
        self.render()

    def toggle_auto_watch(self, checked):
        self.base_store.set("auto_watch_quota", checked)
        self.refresh()
        self.render()

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
        self.connection.setText(self.text("saved"))
        self.refresh()

    def change_agent(self):
        self.store.set("enabled", False)
        self.agent = self.agents.currentData()
        self.base_store.set("agent", self.agent)
        self.store = selected_store(self.base_store, self.agent)
        self.store.set("enabled", False)
        self.rows, self.cursor = [], None
        self.checked_ids.clear()
        for widget, key in self.translated:
            widget.setText(self.text(key))
        self.connection.setText(self.text("unknown"))
        self.refresh()
        self.render()

    def help(self):
        QMessageBox.information(self, self.text("help"), self.text("help_text"))

    def refresh(self):
        if self.worker:
            self.worker.request("refresh")
            self.worker.request("threads")

    def load_more(self):
        if self.worker and self.cursor:
            self.worker.request("threads", self.cursor)

    def visible_rows(self):
        query = self.search.text().strip().casefold()
        return [row for row in self.rows if not query or query in " ".join(
            str(row.get(key) or "") for key in ("name", "id", "cwd")).casefold()]

    def selected(self):
        return [row["id"] for row in self.visible_rows() if row["id"] in self.checked_ids]

    def selection_changed(self, item):
        if item.column() != 0:
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

    def watch_selected(self):
        for tid in self.selected():
            self.store.watch(tid)
        if self.worker:
            self.worker.request("refresh")
        self.render()

    def unwatch_selected(self):
        for tid in self.selected():
            self.store.unwatch(tid)
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
                rows = page.get("data", [])
                # Providers can repeat UUIDs within a page as well as across pages.
                self.rows = list({r["id"]: r for r in ((self.rows if append else []) + rows)}.values())
                self.cursor = page.get("nextCursor")
            elif kind == "tick":
                self.latest_tick = data
                error = data.get("error")
                if error and compatibility_code(error):
                    self.connection.setText(self.text("compatibility_error") + " (" + error + ")")
                else:
                    self.connection.setText(self.text(error) if error else self.text("ready").replace("Codex", "OpenCode" if self.agent == "opencode" else "Codex"))
            else:
                if data in ("codex_missing", "another_monitor"):
                    self.connection.setText(self.text(data))
                elif compatibility_code(data):
                    self.connection.setText(self.text("compatibility_error") + " (" + data + ")")
                else:
                    self.connection.setText(self.text("generic_error").replace("Codex", "OpenCode" if self.agent == "opencode" else "Codex") + " (" + data + ")")
                self.connection.setToolTip(data)
            self.render()

    def render(self):
        self.search.setPlaceholderText(self.text("search_sessions"))
        self.session_hint.setText(self.text("hint"))
        enabled = self.store.get("enabled", False)
        self.badge.setText(self.text("monitoring" if enabled else "paused"))
        self.toggle.setText(self.text("pause" if enabled else "start"))
        self.more.setEnabled(bool(self.cursor))
        keeper = window_keeper.status(self.base_store)
        self.keeper_toggle.setVisible(self.agent == "codex")
        self.keeper_status.setVisible(self.agent == "codex" and keeper["enabled"])
        self.keeper_toggle.blockSignals(True)
        self.keeper_toggle.setChecked(keeper["enabled"])
        self.keeper_toggle.blockSignals(False)
        if keeper["enabled"]:
            detail = self.text("keeper_independent")
            current = self.latest_tick.get("window_keeper") or {}
            reason = current.get("reason")
            if reason in ("keeper_waiting_update", "keeper_waiting_quota", "keeper_no_window"):
                detail += " · " + self.text(reason)
            elif keeper.get("next_at"):
                detail += " · " + self.text("keeper_next") + " " + timestamp(keeper["next_at"])
            if keeper.get("last_attempt"):
                detail += " · " + self.text("keeper_last") + " " + self.text("keeper_" + keeper["last_attempt"]["state"])
            self.keeper_status.setText(detail)
        else:
            self.keeper_status.setText(self.text("keeper_off"))
        snapshot = self.store.get("usage", {"windows": []})
        # Rebuild only when quota values or locale change, avoiding focus churn.
        quota_key = (str(snapshot), self.language)
        if getattr(self, "quota_key", None) != quota_key:
            self.quota_key = quota_key
            while self.quota_layout.count():
                item = self.quota_layout.takeAt(0)
                if item.widget():
                    item.widget().hide()
                    item.widget().deleteLater()
            for window in snapshot.get("windows", []) or [None]:
                card = QFrame()
                card.setObjectName("card")
                card_box = QVBoxLayout(card)
                card_box.setContentsMargins(18, 15, 18, 15)
                if window:
                    label = f'{window["bucket"]} · {duration_label(window.get("minutes"), self.language)}'
                    left = max(0, 100 - window["used_percent"])
                    amount = f'{left:g}% {self.text("remaining")}'
                    reset = self.text("reset") + " · " + timestamp(window.get("reset_at"))
                else:
                    label = "OpenCode" if self.agent == "opencode" else "Codex"
                    amount, reset = self.text("unknown"), self.text("quota_not_exposed") if self.agent == "opencode" else "—"
                    left = 0
                card_box.addWidget(QLabel(label))
                number = QLabel(amount)
                number.setObjectName("amount")
                card_box.addWidget(number)
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setValue(int(left))
                bar.setTextVisible(False)
                card_box.addWidget(bar)
                reset_label = QLabel(reset)
                reset_label.setWordWrap(True)
                card_box.addWidget(reset_label)
                card_box.addWidget(QLabel(self.text("usage_age") + " · " + timestamp(snapshot.get("checked_at"))))
                self.quota_layout.addWidget(card)
        watched = {r["id"] for r in self.store.watched()}
        records = self.store.records()
        self.table.setHorizontalHeaderLabels([self.text(k) for k in ("select", "thread", "project", "status")])
        # Checkbox state follows IDs, never row positions or transient row highlights.
        self.checked_ids.intersection_update(row["id"] for row in self.rows)
        self.table.blockSignals(True)
        self.store.remember_sessions(self.rows)
        rows = self.visible_rows()
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
            text = self.text(state)
            if record and record["state"] == "waiting":
                text += " · " + timestamp(record["due"])
            status = QTableWidgetItem(text)
            status.setForeground(QColor("#27272a" if tid in watched else "#71717a"))
            if record:
                status.setToolTip(self.text(record["detail"]) + "\n" + record["id"])
            self.table.setItem(index, 3, status)
            for cell in (name, project, status):
                cell.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.table.blockSignals(False)
        self.selection_controls()
        events = self.store.events()
        self.events.setHorizontalHeaderLabels([self.text(k) for k in ("time", "thread", "event")])
        self.events.setRowCount(len(events))
        names = self.store.session_names()
        for index, event in enumerate(events):
            tid = event["thread_id"]
            title = names.get(tid)
            session = title + "\n" + tid if title else tid or "—"
            for col, text in enumerate((timestamp(event["time"]), session, self.text(event["code"]))):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.events.setItem(index, col, item)

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop.set()
            self.worker.wake.set()
        event.accept()


def main(store=None):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Auto Resume Agent")
    app.setOrganizationName("AutoResumeAgent")
    app.setStyleSheet(STYLE)
    smoke = "--smoke-test" in sys.argv
    if smoke:
        import tempfile
        isolated = tempfile.TemporaryDirectory()
        store = Store(isolated.name)
    window = Window(store or Store(), start_worker=not smoke)
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
