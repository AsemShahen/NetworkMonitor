from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import REFRESH_CHOICES
from ..i18n import get_language, is_rtl, refresh_label, set_language, tr
from .blocked_tab import BlockedTab
from .chart_view import ChartView
from .icons import get_app_icon
from .language import apply_language
from .settings_tab import SettingsTab
from .theme import THEME
from .traffic_table import TrafficFilterProxy, TrafficModel, TrafficTable
from .widgets import Badge, StatCard
from .worker import Worker


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.include_idle = bool(controller.config.get("show_idle", False))
        self._busy = False
        self._last_summary: dict = {}
        self._pending_success = ""
        self._pending_silent = False
        self._thread = QThread(self)
        self._worker = Worker(controller)
        self._worker.moveToThread(self._thread)
        self._worker.snapshot_done.connect(self._on_snapshot)
        self._worker.snapshot_error.connect(self._on_async_error)
        self._worker.action_done.connect(self._on_action_done)
        self._thread.start()

        self.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        self.setWindowTitle(tr("app.window_title"))
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(1180, 780)
        self.setStyleSheet(THEME + self._group_title_style())

        self._build()
        self._wire()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

        self._apply_interval()
        self._update_blocked_tab()
        self.timer.start()

        QTimer.singleShot(600, self.refresh)
        QTimer.singleShot(1800, self.refresh)
        if self.controller.config.get("apply_on_start", False) and self.controller.blocklist.entries:
            QTimer.singleShot(1500, self._apply_blocklist_silent)

    # ------------------------------------------------------------------ build
    def _build(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 10)
        root.setSpacing(14)

        root.addWidget(self._build_header())
        root.addLayout(self._build_cards())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_live_tab(), tr("tab.live"))
        self.tabs.addTab(self._build_chart_tab(), tr("tab.chart"))
        self.blocked_tab = BlockedTab()
        self.tabs.addTab(self.blocked_tab, tr("tab.blocked"))
        self.settings_tab = SettingsTab(self.controller.config)
        self.tabs.addTab(self.settings_tab, tr("tab.settings"))
        root.addWidget(self.tabs, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("app.ready"))

        from PySide6.QtWidgets import QSystemTrayIcon

        from .tray import Tray

        self.tray = Tray(self)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

        self.settings_tab.set_env_text(self._env_text())

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("header")
        lay = QHBoxLayout(header)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(12)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.header_title = QLabel(tr("app.title"))
        self.header_title.setObjectName("appTitle")
        self.header_subtitle = QLabel(tr("app.subtitle"))
        self.header_subtitle.setObjectName("appSubtitle")
        titles.addWidget(self.header_title)
        titles.addWidget(self.header_subtitle)
        lay.addLayout(titles)
        lay.addStretch(1)

        self.engine_badge = Badge(tr("header.detecting"))
        lay.addWidget(self.engine_badge)

        self.interval_label = QLabel(tr("header.interval"))
        self.interval_label.setObjectName("cardHint")
        lay.addWidget(self.interval_label)

        self.interval_combo = QComboBox()
        for ms in REFRESH_CHOICES:
            self.interval_combo.addItem(refresh_label(ms), ms)
        current = int(self.controller.config.get("refresh_ms", 30000))
        idx = next((i for i, ms in enumerate(REFRESH_CHOICES) if ms == current), 2)
        self.interval_combo.setCurrentIndex(idx)
        lay.addWidget(self.interval_combo)

        self.btn_refresh = QPushButton(tr("header.refresh"))
        self.btn_refresh.setProperty("variant", "primary")
        lay.addWidget(self.btn_refresh)
        return header

    def _build_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.card_down = StatCard(tr("card.down.title"), "0 B/s", tr("card.down.hint"), "down")
        self.card_up = StatCard(tr("card.up.title"), "0 B/s", tr("card.up.hint"), "up")
        self.card_total_down = StatCard(
            tr("card.total_down.title"), "0 B", tr("card.total.hint"), "total-down"
        )
        self.card_total_up = StatCard(
            tr("card.total_up.title"), "0 B", tr("card.total.hint"), "total-up"
        )
        self.card_count = StatCard(
            tr("card.count.title"), "0", tr("card.count.hint"), "count"
        )
        self._card_titles = (
            (self.card_down, "card.down.title"),
            (self.card_up, "card.up.title"),
            (self.card_total_down, "card.total_down.title"),
            (self.card_total_up, "card.total_up.title"),
            (self.card_count, "card.count.title"),
        )
        for card in (
            self.card_down,
            self.card_up,
            self.card_total_down,
            self.card_total_up,
            self.card_count,
        ):
            row.addWidget(card, 1)
        return row

    def _build_live_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(tr("live.search"))
        self.filter.setClearButtonEnabled(True)
        tools.addWidget(self.filter, 1)

        self.btn_block = QPushButton(tr("live.block"))
        self.btn_block.setProperty("variant", "danger")
        self.btn_unblock = QPushButton(tr("live.unblock"))
        self.btn_export = QPushButton(tr("live.export"))
        tools.addWidget(self.btn_block)
        tools.addWidget(self.btn_unblock)
        tools.addWidget(self.btn_export)
        lay.addLayout(tools)

        self.model = TrafficModel()
        self.proxy = TrafficFilterProxy()
        self.proxy.setSourceModel(self.model)
        self.proxy.set_hide_idle(not self.include_idle)
        self.table = TrafficTable()
        self.table.setModel(self.proxy)
        self.table.apply_column_widths()
        self.table.sortByColumn(4, Qt.DescendingOrder)

        self.chart_live = ChartView(window_sec=120)
        self.chart_live.setMinimumHeight(150)

        split = QSplitter(Qt.Vertical)
        split.addWidget(self.table)
        split.addWidget(self.chart_live)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        split.setSizes([460, 190])
        lay.addWidget(split, 1)
        return page

    def _build_chart_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)
        self.chart_title = QLabel(tr("chart.title"))
        self.chart_title.setObjectName("appTitle")
        self.chart_hint = QLabel(tr("chart.hint"))
        self.chart_hint.setObjectName("cardHint")
        lay.addWidget(self.chart_title)
        lay.addWidget(self.chart_hint)
        self.chart_full = ChartView(window_sec=1800)
        lay.addWidget(self.chart_full, 1)
        return page

    # ------------------------------------------------------------------ wiring
    def _wire(self) -> None:
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_block.clicked.connect(self.block_selected)
        self.btn_unblock.clicked.connect(self.unblock_selected)
        self.btn_export.clicked.connect(self.export_names)
        self.filter.textChanged.connect(self.proxy.set_needle)
        self.interval_combo.currentIndexChanged.connect(self._on_header_interval)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self.settings_tab.interval_changed.connect(self._on_settings_interval)
        self.settings_tab.show_idle_changed.connect(self._on_show_idle)
        self.settings_tab.keep_totals_changed.connect(
            lambda v: self.controller.config.set("keep_totals", bool(v))
        )
        self.settings_tab.apply_on_start_changed.connect(
            lambda v: self.controller.config.set("apply_on_start", bool(v))
        )
        self.settings_tab.language_changed.connect(self._on_language_changed)
        self.settings_tab.reset_totals_requested.connect(self._reset_totals)
        self.settings_tab.apply_blocklist_requested.connect(self.apply_blocklist)

        self.blocked_tab.unblock_requested.connect(self._unblock_slug)
        self.blocked_tab.export_requested.connect(self._export_blocklist)
        self.blocked_tab.import_requested.connect(self._import_blocklist)
        self.blocked_tab.apply_requested.connect(self.apply_blocklist)

    # --------------------------------------------------------------- interval
    def _apply_interval(self) -> None:
        ms = int(self.controller.config.get("refresh_ms", 30000))
        if hasattr(self, "timer"):
            self.timer.setInterval(max(1000, ms))

    def _on_header_interval(self) -> None:
        ms = int(self.interval_combo.currentData())
        self.controller.set_refresh_ms(ms)
        self._sync_settings_interval(ms)
        self._apply_interval()

    def _on_settings_interval(self, ms: int) -> None:
        self.controller.set_refresh_ms(ms)
        self.interval_combo.blockSignals(True)
        idx = self.interval_combo.findData(ms)
        if idx >= 0:
            self.interval_combo.setCurrentIndex(idx)
        self.interval_combo.blockSignals(False)
        self._apply_interval()

    def _sync_settings_interval(self, ms: int) -> None:
        idx = self.settings_tab.interval.findData(ms)
        if idx >= 0:
            self.settings_tab.interval.blockSignals(True)
            self.settings_tab.interval.setCurrentIndex(idx)
            self.settings_tab.interval.blockSignals(False)

    def _on_show_idle(self, value: bool) -> None:
        self.include_idle = bool(value)
        self.controller.config.set("show_idle", self.include_idle)
        self.proxy.set_hide_idle(not self.include_idle)
        self.refresh()

    # --------------------------------------------------------------- language
    def _on_language_changed(self, code: str) -> None:
        if code == get_language():
            return
        set_language(code)
        self.controller.config.set("language", code)
        apply_language(QApplication.instance())
        self.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        self.retranslate()
        self.refresh()

    @staticmethod
    def _group_title_style() -> str:
        if is_rtl():
            return ""
        return "\nQGroupBox::title { subcontrol-position: top left; left: 16px; right: auto; }\n"

    def retranslate(self) -> None:
        self.setStyleSheet(THEME + self._group_title_style())
        self.setWindowTitle(tr("app.window_title"))
        self.header_title.setText(tr("app.title"))
        self.header_subtitle.setText(tr("app.subtitle"))
        self.interval_label.setText(tr("header.interval"))
        self.btn_refresh.setText(tr("header.refresh"))
        self.filter.setPlaceholderText(tr("live.search"))
        self.btn_block.setText(tr("live.block"))
        self.btn_unblock.setText(tr("live.unblock"))
        self.btn_export.setText(tr("live.export"))
        self.chart_title.setText(tr("chart.title"))
        self.chart_hint.setText(tr("chart.hint"))

        for i, ms in enumerate(REFRESH_CHOICES):
            self.interval_combo.setItemText(i, refresh_label(ms))

        for i, key in enumerate(("tab.live", "tab.chart", "tab.blocked", "tab.settings")):
            self.tabs.setTabText(i, tr(key))

        for card, key in self._card_titles:
            card.set_title(tr(key))
            card.set_rtl(is_rtl())

        self.model.retranslate()
        self.chart_live.retranslate()
        self.chart_full.retranslate()
        self.blocked_tab.retranslate()
        self.settings_tab.retranslate()
        self.tray.retranslate()
        self.settings_tab.set_env_text(self._env_text())

        if self._last_summary:
            self._render_summary_texts(self._last_summary)
        else:
            self.engine_badge.set_state(tr("header.detecting"))
            self.status.showMessage(tr("app.ready"))
            self.card_down.set_hint(tr("card.down.hint"))
            self.card_up.set_hint(tr("card.up.hint"))
            self.card_total_down.set_hint(tr("card.total.hint"))
            self.card_total_up.set_hint(tr("card.total.hint"))
            self.card_count.set_hint(tr("card.count.hint"))

    # ---------------------------------------------------------------- refresh
    def refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.engine_badge.set_state(tr("status.refreshing"))
        self._worker.request_snapshot.emit(self.include_idle)

    def _on_snapshot(self, rows: list[dict], summary: dict) -> None:
        self._busy = False
        self._last_summary = summary
        self.model.replace(rows)

        from ..util import fmt_bytes, fmt_rate

        self.card_down.set_value(fmt_rate(summary["down_bps"]), tr("card.down.hint"))
        self.card_up.set_value(fmt_rate(summary["up_bps"]), tr("card.up.hint"))
        self.card_total_down.set_value(fmt_bytes(summary["down_total"]), tr("card.total.hint"))
        self.card_total_up.set_value(fmt_bytes(summary["up_total"]), tr("card.total.hint"))
        self.card_count.set_value(
            str(summary["active"]),
            tr("card.count.value_hint", active=summary["active"], count=summary["count"]),
        )

        ts = None
        self.chart_live.add_point(summary["down_bps"], summary["up_bps"], ts)
        self.chart_full.add_point(summary["down_bps"], summary["up_bps"], ts)

        self._render_summary_texts(summary)

    def _render_summary_texts(self, summary: dict) -> None:
        ok = bool(summary.get("engine_ok"))
        state = tr("status.engine.ready" if ok else "status.engine.limited")
        self.engine_badge.set_state(tr("status.engine", state=state), ok)
        self.settings_tab.set_engine_text(summary.get("source", "—"), ok, summary.get("error"))

        err = summary.get("error")
        msg = tr(
            "status.summary",
            active=summary.get("active", 0),
            count=summary.get("count", 0),
            seconds=int(self.controller.config.get("refresh_ms", 30000)) // 1000,
        )
        if err:
            msg += f" • {err}"
        self.status.showMessage(msg)

    def _on_async_error(self, message: str) -> None:
        self._busy = False
        self.engine_badge.set_state(tr("status.engine_error"), False)
        self.status.showMessage(tr("status.error", message=message))
        self.settings_tab.set_engine_text("—", False, message)

    # ----------------------------------------------------------------- actions
    def _selected_row(self) -> dict | None:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        return self.model.row_at(self.proxy.mapToSource(idx))

    def block_selected(self) -> None:
        row = self._selected_row()
        if not row:
            self.status.showMessage(tr("action.choose_app"))
            return
        exe = row.get("exe") or ""
        if not exe:
            QMessageBox.warning(
                self,
                tr("action.block_title"),
                tr("action.block_no_path"),
            )
            return
        name = row.get("name") or os.path.basename(exe)
        if self.controller.config.get("confirm_block", True):
            reply = QMessageBox.question(
                self,
                tr("action.confirm_block_title"),
                tr("action.confirm_block", name=name, exe=exe),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.status.showMessage(tr("action.blocking", name=name))
        self._run_action(lambda: self.controller.block(exe, name), tr("action.block_success"))

    def unblock_selected(self) -> None:
        row = self._selected_row()
        if not row:
            self.status.showMessage(tr("action.choose_app"))
            return
        exe = row.get("exe") or ""
        if not exe:
            self.status.showMessage(tr("error.no_exe_short"))
            return
        self.status.showMessage(tr("action.unblocking", name=row.get("name")))
        self._run_action(lambda: self.controller.unblock(exe), tr("action.unblock_success"))

    def _unblock_slug(self, slug: str) -> None:
        self.status.showMessage(tr("action.unblocking_generic"))
        self._run_action(lambda: self.controller.unblock_slug(slug), tr("action.unblock_success"))

    def apply_blocklist(self) -> None:
        if not self.controller.blocklist.entries:
            self.status.showMessage(tr("action.blocklist_empty"))
            return
        self.status.showMessage(tr("action.applying"))
        self._run_action(self.controller.apply_blocklist, tr("action.apply_success"))

    def _apply_blocklist_silent(self) -> None:
        if not self.controller.blocklist.entries:
            return
        self._run_action(self.controller.apply_blocklist, "", silent=True)

    def _run_action(self, fn, success_msg: str, silent: bool = False) -> None:
        self._pending_success = success_msg
        self._pending_silent = silent
        self._worker.request_action.emit(fn)

    def _on_action_done(self, ok: bool, message: str) -> None:
        success_msg = self._pending_success or tr("action.default_success")
        silent = self._pending_silent
        self._pending_success = ""
        self._pending_silent = False
        if silent:
            if not ok:
                self.status.showMessage(
                    tr("action.apply_auto_error", message=message or tr("action.unknown_error"))
                )
            self._update_blocked_tab()
            return
        if ok:
            self.status.showMessage(success_msg)
            QMessageBox.information(self, tr("action.done_title"), message or success_msg)
        else:
            self.status.showMessage(tr("action.failed", message=message or tr("action.unknown_error")))
            QMessageBox.warning(
                self, tr("action.failed_title"), message or tr("action.unknown_error")
            )
        self._update_blocked_tab()
        self.refresh()

    def _open_context_menu(self, pos) -> None:
        idx = self.table.indexAt(pos)
        if not idx.isValid():
            return
        self.table.setCurrentIndex(idx)
        row = self._selected_row()
        if not row:
            return
        from PySide6.QtWidgets import QMenu

        menu = QMenu(self)
        if row.get("blocked"):
            act_toggle = QAction(tr("context.unblock"), self)
            act_toggle.triggered.connect(self.unblock_selected)
        else:
            act_toggle = QAction(tr("context.block"), self)
            act_toggle.triggered.connect(self.block_selected)
        menu.addAction(act_toggle)

        act_copy = QAction(tr("context.copy"), self)
        act_copy.setEnabled(bool(row.get("exe")))
        act_copy.triggered.connect(lambda: self._copy_path(row.get("exe") or ""))
        menu.addAction(act_copy)

        menu.addSeparator()
        act_export = QAction(tr("context.export"), self)
        act_export.triggered.connect(self.export_names)
        menu.addAction(act_export)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_path(self, path: str) -> None:
        if not path:
            return
        QApplication.clipboard().setText(path)
        self.status.showMessage(tr("status.copied"))

    # ------------------------------------------------------------------ export
    def _visible_names(self) -> list[str]:
        names: list[str] = []
        for r in range(self.proxy.rowCount()):
            src = self.proxy.mapToSource(self.proxy.index(r, 0))
            row = self.model.row_at(src)
            if not row:
                continue
            name = str(row.get("name") or "").strip()
            if name and name not in names:
                names.append(name)
        return names

    def export_names(self) -> None:
        names = self._visible_names()
        if not names:
            self.status.showMessage(tr("export.empty"))
            return
        default = str(Path.home() / "Desktop" / tr("export.default_name"))
        path, _ = QFileDialog.getSaveFileName(
            self, tr("export.title"), default, tr("export.filter")
        )
        if not path:
            return
        try:
            Path(path).write_text("، ".join(names), encoding="utf-8")
            self.status.showMessage(tr("export.done", path=path, count=len(names)))
        except OSError as exc:
            QMessageBox.warning(self, tr("export.failed_title"), str(exc))

    def _export_blocklist(self) -> None:
        default = str(Path.home() / "blocklist-backup.json")
        path, _ = QFileDialog.getSaveFileName(
            self, tr("export.blocklist_title"), default, "JSON (*.json)"
        )
        if not path:
            return
        try:
            self.controller.blocklist.export_to(Path(path))
            self.status.showMessage(tr("export.blocklist_done"))
        except OSError as exc:
            QMessageBox.warning(self, tr("export.failed_title"), str(exc))

    def _import_blocklist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("import.title"), str(Path.home()), "JSON (*.json)"
        )
        if not path:
            return
        try:
            count = self.controller.blocklist.import_from(Path(path))
            self._update_blocked_tab()
            QMessageBox.information(
                self, tr("import.done_title"), tr("import.done", count=count)
            )
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, tr("import.failed_title"), str(exc))

    # ---------------------------------------------------------------- settings
    def _reset_totals(self) -> None:
        reply = QMessageBox.question(
            self,
            tr("reset.title"),
            tr("reset.question"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.controller.reset_totals()
            self.chart_live.clear()
            self.chart_full.clear()
            self.status.showMessage(tr("reset.done"))
            self.refresh()

    def _update_blocked_tab(self) -> None:
        if hasattr(self, "blocked_tab"):
            self.blocked_tab.set_entries(self.controller.blocklist.list())

    def _on_tab_changed(self, index: int) -> None:
        if self.tabs.widget(index) is self.blocked_tab:
            self._update_blocked_tab()

    # -------------------------------------------------------------------- misc
    def _env_text(self) -> str:
        ss = shutil.which("ss")
        nft = shutil.which("nft")
        cgroup2 = os.path.exists("/sys/fs/cgroup/cgroup.controllers")
        available = tr("env.available")
        unavailable = tr("env.unavailable")
        return tr(
            "env.text",
            python=platform.python_version(),
            qt=QtCore.qVersion(),
            ss=available if ss else unavailable,
            nft=available if nft else unavailable,
            cgroup=available if cgroup2 else unavailable,
        )

    def shutdown(self) -> None:
        if getattr(self, "_shut", False):
            return
        self._shut = True
        self.timer.stop()
        self._thread.quit()
        self._thread.wait(3000)
        self.controller.shutdown()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.shutdown()
        super().closeEvent(event)
