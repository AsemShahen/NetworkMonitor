from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import time
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
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from .. import collector_service
from ..collector_status import read_collector_status
from ..config import REFRESH_CHOICES, install_autostart
from ..i18n import get_language, is_rtl, refresh_label, set_language, tr
from ..util import short_path
from . import theme
from .blocked_tab import BlockedTab
from .chart_view import ChartView
from .icons import get_app_icon
from .language import apply_language
from .security_tab import SecurityTab
from .security_workers import FileHashThread, IPReputationThread
from .settings_tab import SettingsTab
from .traffic_table import TrafficFilterProxy, TrafficModel, TrafficTable
from .update_worker import UpdateCheckThread, UpdateInstallThread
from .usage_tab import UsageTab
from .widgets import Badge, StatCard
from .worker import Worker


class MainWindow(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.include_idle = bool(controller.config.get("show_idle", False))
        self._busy = False
        self._really_quit = False
        self._tray_hint_shown = False
        self._last_summary: dict = {}
        self._pending_success = ""
        self._pending_silent = False
        self._update_thread = None
        self._install_thread = None
        self._ip_thread = None
        self._hash_thread = None
        self._last_ip_scan = 0.0
        self._collector_changing = False
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
        self.setStyleSheet(theme.stylesheet() + self._group_title_style())

        self._build()
        self._wire()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

        self._apply_interval()
        self._update_blocked_tab()
        self.timer.start()

        self._collector_timer = QTimer(self)
        self._collector_timer.timeout.connect(self._refresh_collector_status)
        self._collector_timer.start(3000)
        self.settings_tab.set_collector_available(collector_service.available())
        QTimer.singleShot(700, self._init_collector)

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
        self.security_tab = SecurityTab(self.controller.config)
        self.tabs.addTab(self.security_tab, tr("tab.security"))
        self.usage_tab = UsageTab(self.controller)
        self.tabs.addTab(self.usage_tab, tr("tab.usage"))
        self.blocked_tab = BlockedTab()
        self.tabs.addTab(self.blocked_tab, tr("tab.blocked"))
        self.settings_tab = SettingsTab(self.controller.config)
        self.tabs.addTab(self.settings_tab, tr("tab.settings"))
        root.addWidget(self.tabs, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(tr("app.ready"))

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
        self.card_month = StatCard(
            tr("card.month.title"), "0 B", tr("card.month.hint", down="0 B", up="0 B"), "month"
        )
        self._card_titles = (
            (self.card_down, "card.down.title"),
            (self.card_up, "card.up.title"),
            (self.card_total_down, "card.total_down.title"),
            (self.card_total_up, "card.total_up.title"),
            (self.card_count, "card.count.title"),
            (self.card_month, "card.month.title"),
        )
        for card in (
            self.card_down,
            self.card_up,
            self.card_total_down,
            self.card_total_up,
            self.card_count,
            self.card_month,
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
        self.settings_tab.theme_changed.connect(self._on_theme_changed)
        self.settings_tab.reset_totals_requested.connect(self._reset_totals)
        self.settings_tab.apply_blocklist_requested.connect(self.apply_blocklist)
        self.settings_tab.keep_usage_changed.connect(self._on_keep_usage_changed)
        self.settings_tab.background_collector_changed.connect(
            self._on_background_collector_changed
        )
        self.settings_tab.group_cgroups_changed.connect(self._on_group_cgroups_changed)
        self.settings_tab.autostart_changed.connect(self._on_autostart_changed)
        self.settings_tab.minimize_to_tray_changed.connect(self._on_minimize_to_tray_changed)
        self.settings_tab.update_requested.connect(self._check_updates)

        self.usage_tab.export_requested.connect(self.export_usage)
        self.usage_tab.reset_requested.connect(self._reset_usage)

        self.settings_tab.security_settings_changed.connect(
            self._on_security_settings_changed
        )
        self.security_tab.check_ip_requested.connect(self._start_ip_scan)
        self.security_tab.check_hash_requested.connect(self._start_hash_check)
        self.security_tab.block_app_requested.connect(self._block_app_from_security)
        self.security_tab.block_ip_requested.connect(self._block_ip)
        self.security_tab.unblock_ip_requested.connect(self._unblock_ip)
        self.security_tab.clear_requested.connect(self._clear_security_alerts)

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

    # ----------------------------------------------------------------- theme
    def _on_theme_changed(self, mode: str) -> None:
        self.controller.config.set("theme", mode)
        theme.apply(QApplication.instance(), mode)
        self.setStyleSheet(theme.stylesheet() + self._group_title_style())
        self.chart_live.apply_theme()
        self.chart_full.apply_theme()
        self.usage_tab.apply_theme()
        self.security_tab.apply_theme()
        self.table.viewport().update()
        self.blocked_tab.table.viewport().update()

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
        self.setStyleSheet(theme.stylesheet() + self._group_title_style())
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

        for i, key in enumerate(
            (
                "tab.live",
                "tab.chart",
                "tab.security",
                "tab.usage",
                "tab.blocked",
                "tab.settings",
            )
        ):
            self.tabs.setTabText(i, tr(key))

        for card, key in self._card_titles:
            card.set_title(tr(key))
            card.set_rtl(is_rtl())

        self.model.retranslate()
        self.chart_live.retranslate()
        self.chart_full.retranslate()
        self.usage_tab.retranslate()
        self.security_tab.retranslate()
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
            self.card_month.set_hint(tr("card.month.hint", down="0 B", up="0 B"))

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
            tr(
                "card.count.value_hint",
                active=summary["active"],
                count=summary["count"],
                processes=summary.get("processes", summary["count"]),
            ),
        )
        month_down = int(summary.get("month_down", 0))
        month_up = int(summary.get("month_up", 0))
        self.card_month.set_value(
            fmt_bytes(month_down + month_up),
            tr(
                "card.month.hint",
                down=fmt_bytes(month_down),
                up=fmt_bytes(month_up),
            ),
        )
        if self.tabs.currentWidget() is self.usage_tab:
            self.usage_tab.refresh()

        self.security_tab.update_report(summary.get("security") or {})
        self.security_tab.set_blocked_ips(self.controller.security_store.blocked_ips())
        self._maybe_auto_ip_check(summary.get("security") or {})

        ts = None
        self.chart_live.add_point(summary["down_bps"], summary["up_bps"], ts)
        self.chart_full.add_point(summary["down_bps"], summary["up_bps"], ts)

        self._render_summary_texts(summary)

    def _render_summary_texts(self, summary: dict) -> None:
        ok = bool(summary.get("engine_ok"))
        state = tr("status.engine.ready" if ok else "status.engine.limited")
        self.engine_badge.set_state(tr("status.engine", state=state), ok)
        self.settings_tab.set_engine_text(summary.get("source", "—"), ok, summary.get("error"))
        self.settings_tab.set_diagnostics(summary.get("diagnostics") or {})

        err = summary.get("error")
        msg = tr(
            "status.summary",
            active=summary.get("active", 0),
            count=summary.get("count", 0),
            processes=summary.get("processes", summary.get("count", 0)),
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
        self.settings_tab.set_diagnostics({"error": message})

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

        act_hash = QAction(tr("context.hash"), self)
        act_hash.setEnabled(bool(row.get("exe")))
        act_hash.triggered.connect(
            lambda: self._start_hash_check(
                str(row.get("exe") or ""), str(row.get("name") or "")
            )
        )
        menu.addAction(act_hash)

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

    # --------------------------------------------------------------- security
    def _on_security_settings_changed(self, values) -> None:
        if not isinstance(values, dict):
            return
        self.controller.config.data.update(values)
        self.controller.config.save()

    def _security_key(self, provider: str = "") -> str:
        provider = provider or str(
            self.controller.config.get("security_ip_provider", "abuseipdb")
        )
        if provider == "virustotal":
            return str(self.controller.config.get("security_virustotal_key", "") or "")
        return str(self.controller.config.get("security_abuseipdb_key", "") or "")

    def _maybe_auto_ip_check(self, report: dict) -> None:
        if self.tabs.currentWidget() is not self.security_tab:
            return
        if not bool(self.controller.config.get("security_auto_ip_check", False)):
            return
        if self._ip_thread is not None and self._ip_thread.isRunning():
            return
        if time.time() - self._last_ip_scan < 300:
            return
        ips = [
            str(item.get("ip") or "")
            for item in (report.get("external_ips") or [])
            if item.get("ip")
        ][:20]
        if not ips or not self._security_key():
            return
        self.status.showMessage(tr("security.status.auto"))
        self._start_ip_scan(ips)

    def _start_ip_scan(self, ips: list[str]) -> None:
        if self._ip_thread is not None and self._ip_thread.isRunning():
            self.status.showMessage(tr("security.status.scanning"))
            return
        unique = []
        for ip in ips or []:
            value = str(ip or "").strip()
            if value and value not in unique:
                unique.append(value)
        if not unique:
            self.status.showMessage(tr("security.status.no_ips"))
            return
        provider = str(self.controller.config.get("security_ip_provider", "abuseipdb"))
        api_key = self._security_key(provider)
        if not api_key:
            QMessageBox.information(
                self,
                tr("security.no_key_title"),
                tr("security.no_key_body"),
            )
            self.tabs.setCurrentWidget(self.settings_tab)
            return
        if provider == "virustotal":
            # Respect the free-tier rate limit while keeping the wait bounded.
            unique = unique[:8]
        self._last_ip_scan = time.time()
        self.security_tab.set_scanning(True)
        self.status.showMessage(tr("security.status.scan_started", count=len(unique)))
        thread = IPReputationThread(
            unique,
            provider,
            api_key,
            self.controller.security_store,
            self,
        )
        self._ip_thread = thread
        thread.result_ready.connect(self._on_ip_results)
        thread.progress.connect(
            lambda done, total, ip: self.status.showMessage(
                f"{tr('security.status.scanning')} {done}/{total} — {ip}"
            )
        )
        thread.finished.connect(self._on_ip_finished)
        thread.start()

    def _on_ip_results(self, results) -> None:
        self.security_tab.set_reputation_results(list(results or []))
        self.status.showMessage(
            tr("security.status.scan_done", count=len(results or []))
        )

    def _on_ip_finished(self) -> None:
        self._ip_thread = None
        self.security_tab.set_scanning(False)

    def _start_hash_check(self, path: str, name: str = "") -> None:
        if not path:
            QMessageBox.warning(
                self,
                tr("security.hash_failed_title"),
                tr("error.no_exe_short"),
            )
            return
        if self._hash_thread is not None and self._hash_thread.isRunning():
            self.status.showMessage(tr("security.status.scanning"))
            return
        provider = str(
            self.controller.config.get("security_hash_provider", "malwarebazaar")
        )
        api_key = ""
        if provider == "virustotal":
            api_key = str(
                self.controller.config.get("security_virustotal_key", "") or ""
            )
            if not api_key:
                QMessageBox.information(
                    self,
                    tr("security.no_key_title"),
                    tr("security.no_key_body"),
                )
                self.tabs.setCurrentWidget(self.settings_tab)
                return
        self.status.showMessage(
            tr("security.status.hashing", name=name or os.path.basename(path))
        )
        thread = FileHashThread(
            path,
            provider,
            api_key,
            self.controller.security_store,
            self,
        )
        self._hash_thread = thread
        thread.result_ready.connect(self._on_hash_result)
        thread.finished.connect(self._on_hash_finished)
        thread.start()

    def _on_hash_result(self, result) -> None:
        data = dict(result or {})
        self.security_tab.set_hash_result(data)
        if not data.get("ok"):
            message = tr(
                str(data.get("error_key") or "security.error.network"),
                **dict(data.get("error_args") or {}),
            )
            QMessageBox.warning(self, tr("security.hash_failed_title"), message)
            return
        if data.get("malicious"):
            message = tr(
                "security.hash.malicious",
                path=short_path(str(data.get("path") or ""), 80),
                detections=int(data.get("detections") or 0),
                total=int(data.get("total") or 0),
            )
            QMessageBox.warning(self, tr("security.hash_title"), message)
        else:
            message = tr(
                "security.hash.safe",
                path=short_path(str(data.get("path") or ""), 80),
            )
            QMessageBox.information(self, tr("security.hash_title"), message)
        self.status.showMessage(message)

    def _on_hash_finished(self) -> None:
        self._hash_thread = None

    def _block_app_from_security(self, exe: str, name: str) -> None:
        if not exe:
            QMessageBox.warning(self, tr("action.block_title"), tr("action.block_no_path"))
            return
        if self.controller.config.get("confirm_block", True):
            reply = QMessageBox.question(
                self,
                tr("security.block_title"),
                tr(
                    "security.confirm_block",
                    name=name or os.path.basename(exe),
                    exe=exe,
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.status.showMessage(
            tr("action.blocking", name=name or os.path.basename(exe))
        )
        self._run_action(
            lambda: self.controller.block(exe, name),
            tr("security.block_success"),
        )

    def _block_ip(self, ip: str) -> None:
        if not ip:
            return
        if self.controller.security_store.is_blocked_ip(ip):
            self.status.showMessage(tr("security.status.blocked_ip", ip=ip))
            return
        reply = QMessageBox.question(
            self,
            tr("security.confirm_block_ip_title"),
            tr("security.confirm_block_ip", ip=ip),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.status.showMessage(
            tr("action.blocking", name=ip)
        )
        self._run_action(
            lambda: self.controller.block_ip(ip),
            tr("security.block_ip_success"),
        )

    def _unblock_ip(self, ip: str) -> None:
        if not ip:
            return
        self._run_action(
            lambda: self.controller.unblock_ip(ip),
            tr("security.unblock_ip_success"),
        )

    def _clear_security_alerts(self) -> None:
        reply = QMessageBox.question(
            self,
            tr("security.clear_confirm_title"),
            tr("security.clear_confirm"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.controller.clear_security_history()
        if isinstance(self._last_summary, dict):
            self._last_summary["security"] = {}
        self.security_tab.update_report({})
        self.status.showMessage(tr("security.cleared"))

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

    # ---------------------------------------------------------------- updates
    def _check_updates(self) -> None:
        if self._update_thread is not None and self._update_thread.isRunning():
            return
        if self._install_thread is not None and self._install_thread.isRunning():
            return
        self.settings_tab.set_update_status(tr("update.checking"), busy=True)
        self.status.showMessage(tr("update.checking"))
        thread = UpdateCheckThread(__version__, self)
        self._update_thread = thread
        thread.result.connect(self._on_update_checked)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_update_checked(self, info, error: str) -> None:
        self._update_thread = None
        if error:
            self.settings_tab.set_update_status(
                tr("update.failed", message=error), busy=False
            )
            self.status.showMessage(tr("update.failed", message=error))
            return
        if info is None:
            message = tr("update.latest", version=__version__)
            self.settings_tab.set_update_status(message, busy=False)
            self.status.showMessage(message)
            return

        if info.install_type == "distro":
            message = tr("update.distro_managed", version=info.version)
            self.settings_tab.set_update_status(message, busy=False)
            self.status.showMessage(message)
            QMessageBox.information(
                self,
                tr("update.available_title"),
                message,
            )
            return

        kind = tr(f"update.type.{info.install_type}")
        self.settings_tab.set_update_status(
            tr("update.available", version=info.version), busy=False
        )
        answer = QMessageBox.question(
            self,
            tr("update.available_title"),
            tr(
                "update.available_body",
                version=info.version,
                type=kind,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if answer == QMessageBox.Yes:
            self._install_update(info)

    def _install_update(self, info) -> None:
        if self._install_thread is not None and self._install_thread.isRunning():
            return
        self.settings_tab.set_update_status(tr("update.downloading_checksums"), busy=True)
        self.status.showMessage(tr("update.downloading_checksums"))
        thread = UpdateInstallThread(info, self)
        self._install_thread = thread
        thread.status.connect(self._on_update_progress)
        thread.result.connect(self._on_update_installed)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_update_progress(self, message: str) -> None:
        self.settings_tab.set_update_status(message, busy=True)
        self.status.showMessage(message)

    def _on_update_installed(self, ok: bool, message: str) -> None:
        self._install_thread = None
        if ok:
            self.settings_tab.set_update_status(message, busy=False)
            self.status.showMessage(message)
            QMessageBox.information(
                self,
                tr("update.done_title"),
                tr("update.done_body", message=message),
            )
        else:
            text = tr("update.failed", message=message)
            self.settings_tab.set_update_status(text, busy=False)
            self.status.showMessage(text)
            QMessageBox.warning(self, tr("update.failed_title"), message)

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
        if hasattr(self, "security_tab"):
            self.security_tab.set_blocked_ips(
                self.controller.security_store.blocked_ips()
            )

    def _on_tab_changed(self, index: int) -> None:
        if self.tabs.widget(index) is self.blocked_tab:
            self._update_blocked_tab()
        elif self.tabs.widget(index) is self.security_tab:
            self.security_tab.update_report(
                (self._last_summary or {}).get("security") or {}
            )
            self.security_tab.set_blocked_ips(
                self.controller.security_store.blocked_ips()
            )
            self._maybe_auto_ip_check(
                (self._last_summary or {}).get("security") or {}
            )
        elif self.tabs.widget(index) is self.usage_tab:
            self.usage_tab.refresh_months()
            self.usage_tab.refresh()

    # -------------------------------------------------------------------- misc
    def _env_text(self) -> str:
        from ..collectors.traffic import find_ss

        ss = find_ss()
        nft = shutil.which("nft")
        cgroup2 = os.path.exists("/sys/fs/cgroup/cgroup.controllers")
        try:
            netlink = importlib.util.find_spec("pyroute2") is not None
        except (ImportError, ValueError):
            netlink = False
        available = tr("env.available")
        unavailable = tr("env.unavailable")
        return tr(
            "env.text",
            python=platform.python_version(),
            qt=QtCore.qVersion(),
            netlink=available if netlink else unavailable,
            ss=ss or unavailable,
            nft=available if nft else unavailable,
            cgroup=available if cgroup2 else unavailable,
        )

    def shutdown(self) -> None:
        if getattr(self, "_shut", False):
            return
        self._shut = True
        self.timer.stop()
        if hasattr(self, "_collector_timer"):
            self._collector_timer.stop()
        for thread in (self._ip_thread, self._hash_thread):
            if thread is not None and thread.isRunning():
                thread.requestInterruption()
        for thread in (self._ip_thread, self._hash_thread):
            if thread is not None and thread.isRunning():
                thread.wait(10000)
        for thread in (self._update_thread, self._install_thread):
            if thread is not None and thread.isRunning():
                thread.wait(3000)
        self._thread.quit()
        self._thread.wait(3000)
        self.controller.shutdown()

    def closeEvent(self, event) -> None:  # noqa: N802
        if (
            not self._really_quit
            and bool(self.controller.config.get("minimize_to_tray", False))
            and self.tray.isVisible()
        ):
            event.ignore()
            self.hide()
            if not self._tray_hint_shown:
                self.tray.showMessage(
                    tr("tray.hidden_title"),
                    tr("tray.hidden"),
                    QSystemTrayIcon.Information,
                    3000,
                )
                self._tray_hint_shown = True
            return
        self.shutdown()
        super().closeEvent(event)

    def quit_from_tray(self) -> None:
        self._really_quit = True
        self.close()

    def show_usage_tab(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.tabs.setCurrentWidget(self.usage_tab)

    # ------------------------------------------------------- background collector
    def _collector_enabled(self) -> bool:
        return bool(self.controller.config.get("background_collector", False))

    def _set_background_checkbox(self, checked: bool) -> None:
        box = self.settings_tab.background_collector
        box.blockSignals(True)
        box.setChecked(bool(checked))
        box.blockSignals(False)

    def _init_collector(self) -> None:
        available = collector_service.available()
        self.settings_tab.set_collector_available(available)
        if not self._collector_enabled():
            self._refresh_collector_status()
            return
        if not available:
            self._revert_collector_to_ui(tr("collector.status.unavailable"), silent=True)
            return
        # The controller starts in read-only mode when the collector is enabled.
        # Make sure the generated unit still points at this installation (an
        # AppImage path or a package update may have changed).
        self._start_collector(silent=True)

    def _start_collector(self, silent: bool = False) -> bool:
        try:
            collector_service.enable()
        except Exception as exc:  # noqa: BLE001
            self._revert_collector_to_ui(str(exc), silent=silent)
            return False
        self.controller.config.set("background_collector", True)
        self._set_background_checkbox(True)
        self.settings_tab.set_collector_status("starting")
        self.status.showMessage(tr("collector.enabled"))
        QTimer.singleShot(1200, self._refresh_collector_status)
        return True

    def _revert_collector_to_ui(self, reason: str, silent: bool = False) -> None:
        self.controller.config.set("background_collector", False)
        self._set_background_checkbox(False)
        acquired = self.controller.set_usage_writer(True, timeout=1.0)
        self.settings_tab.set_collector_status("error", error=reason)
        if not acquired:
            self.settings_tab.set_collector_status("error", error=tr("collector.lock_failed"))
        if not silent:
            message = reason if acquired else tr("collector.lock_failed")
            QMessageBox.warning(
                self,
                tr("collector.failed_title"),
                tr("collector.failed", message=message),
            )

    def _refresh_collector_status(self) -> None:
        if self._collector_changing:
            return
        status = read_collector_status()
        state = str(status.get("state") or "unknown")
        age = float(status.get("age", 0.0) or 0.0)
        if state == "running" and not status.get("running"):
            state = "stopped"
        if state in {"starting", "blocked"} and age > 60.0:
            state = "stopped"
        updated = float(status.get("updated", 0.0) or 0.0)
        error = str(status.get("error") or "")
        self.settings_tab.set_collector_status(state, updated=updated, error=error)

    def _on_background_collector_changed(self, value: bool) -> None:
        if self._collector_changing:
            return
        self._collector_changing = True
        self.settings_tab.set_collector_busy(True)
        try:
            if value:
                if not collector_service.available():
                    self._set_background_checkbox(False)
                    self.settings_tab.set_collector_status(
                        "error", error=tr("collector.status.unavailable")
                    )
                    QMessageBox.warning(
                        self,
                        tr("collector.failed_title"),
                        tr("collector.failed", message=tr("collector.status.unavailable")),
                    )
                    return
                # Release the UI lock before systemd starts the collector.
                self.controller.set_usage_writer(False)
                self._start_collector()
            else:
                try:
                    collector_service.disable()
                except Exception as exc:  # noqa: BLE001
                    self.controller.config.set("background_collector", True)
                    self._set_background_checkbox(True)
                    self.settings_tab.set_collector_status("error", error=str(exc))
                    QMessageBox.warning(
                        self,
                        tr("collector.failed_title"),
                        tr("collector.failed", message=str(exc)),
                    )
                    return
                acquired = self.controller.set_usage_writer(True, timeout=4.0)
                self.controller.config.set("background_collector", False)
                self._set_background_checkbox(False)
                if acquired:
                    self.settings_tab.set_collector_status("stopped")
                    self.status.showMessage(tr("collector.disabled"))
                else:
                    self.settings_tab.set_collector_status(
                        "error", error=tr("collector.lock_failed")
                    )
                    QMessageBox.warning(
                        self,
                        tr("collector.failed_title"),
                        tr("collector.failed", message=tr("collector.lock_failed")),
                    )
        finally:
            self.settings_tab.set_collector_busy(False)
            self._collector_changing = False
            self._refresh_collector_status()

    def _on_keep_usage_changed(self, value: bool) -> None:
        self.controller.config.set("keep_usage", bool(value))
        self.usage_tab.refresh()

    def _on_group_cgroups_changed(self, value: bool) -> None:
        self.controller.config.set("group_cgroups", bool(value))
        self.refresh()

    def _on_autostart_changed(self, value: bool) -> None:
        self.controller.config.set("autostart", bool(value))
        try:
            path = install_autostart(bool(value))
        except OSError as exc:
            QMessageBox.warning(self, tr("autostart.disabled"), str(exc))
            return
        if value:
            self.status.showMessage(tr("autostart.enabled", path=path))
        else:
            self.status.showMessage(tr("autostart.disabled"))

    def _on_minimize_to_tray_changed(self, value: bool) -> None:
        self.controller.config.set("minimize_to_tray", bool(value))

    def _reset_usage(self, month: str) -> None:
        reply = QMessageBox.question(
            self,
            tr("usage.reset_title"),
            tr("usage.reset_question", month=month),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        if self.controller.usage.is_writer:
            self.controller.reset_usage_month(month)
        else:
            if not self._collector_enabled() or not collector_service.available():
                QMessageBox.warning(
                    self,
                    tr("collector.failed_title"),
                    tr("collector.failed", message=tr("collector.lock_failed")),
                )
                return
            try:
                collector_service.disable()
                if not self.controller.set_usage_writer(True, timeout=4.0):
                    self._revert_collector_to_ui(tr("collector.lock_failed"))
                    return
            except Exception as exc:  # noqa: BLE001
                self._revert_collector_to_ui(str(exc))
                return
            try:
                self.controller.reset_usage_month(month)
            finally:
                self.controller.set_usage_writer(False)
                try:
                    collector_service.enable()
                except Exception as exc:  # noqa: BLE001
                    self._revert_collector_to_ui(str(exc))
        self.usage_tab.refresh_months()
        self.usage_tab.refresh()
        self.status.showMessage(tr("usage.reset_done", month=month))
        self.refresh()

    def export_usage(self, month: str) -> None:
        default = str(Path.home() / f"network-usage-{month}.csv")
        path, _ = QFileDialog.getSaveFileName(
            self, tr("usage.export_title"), default, "CSV (*.csv)"
        )
        if not path:
            return
        try:
            count = self.controller.export_usage(Path(path), month)
            self.status.showMessage(tr("usage.export_done", path=path, count=count))
        except OSError as exc:
            QMessageBox.warning(self, tr("export.failed_title"), str(exc))
