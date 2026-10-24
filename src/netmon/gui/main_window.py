from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path

from PySide6 import QtCore
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
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

from .blocked_tab import BlockedTab
from .chart_view import ChartView
from .icons import get_app_icon
from .settings_tab import INTERVALS, SettingsTab
from .theme import THEME
from .traffic_table import COLUMNS, TrafficFilterProxy, TrafficModel, TrafficTable
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

        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("Network Monitor — رصد حركة الإنترنت لكل تطبيق")
        self.setWindowIcon(get_app_icon())
        self.setMinimumSize(1180, 780)
        self.setStyleSheet(THEME)

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
        self.tabs.addTab(self._build_live_tab(), "الرصد المباشر")
        self.tabs.addTab(self._build_chart_tab(), "الرسم البياني")
        self.blocked_tab = BlockedTab()
        self.tabs.addTab(self.blocked_tab, "التطبيقات المحظورة")
        self.settings_tab = SettingsTab(self.controller.config)
        self.tabs.addTab(self.settings_tab, "الإعدادات")
        root.addWidget(self.tabs, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("جاهز — بانتظار أول تحديث…")

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
        title = QLabel("Network Monitor")
        title.setObjectName("appTitle")
        subtitle = QLabel("رصد حركة الإنترنت لكل تطبيق وحظره فوراً")
        subtitle.setObjectName("appSubtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        lay.addLayout(titles)
        lay.addStretch(1)

        self.engine_badge = Badge("تحديد المحرك…")
        lay.addWidget(self.engine_badge)

        interval_label = QLabel("التحديث كل:")
        interval_label.setObjectName("cardHint")
        lay.addWidget(interval_label)

        self.interval_combo = QComboBox()
        for label, ms in INTERVALS:
            self.interval_combo.addItem(label, ms)
        current = int(self.controller.config.get("refresh_ms", 30000))
        idx = next((i for i, (_, ms) in enumerate(INTERVALS) if ms == current), 2)
        self.interval_combo.setCurrentIndex(idx)
        lay.addWidget(self.interval_combo)

        self.btn_refresh = QPushButton("تحديث الآن")
        self.btn_refresh.setProperty("variant", "primary")
        lay.addWidget(self.btn_refresh)
        return header

    def _build_cards(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.card_down = StatCard("التحميل الحالي", "0 B/s", "مجموع كل التطبيقات", "down")
        self.card_up = StatCard("الرفع الحالي", "0 B/s", "مجموع كل التطبيقات", "up")
        self.card_total_down = StatCard("إجمالي التحميل", "0 B", "منذ بدء الجلسة", "total-down")
        self.card_total_up = StatCard("إجمالي الرفع", "0 B", "منذ بدء الجلسة", "total-up")
        self.card_count = StatCard("تطبيقات نشطة", "0", "تستخدم الشبكة الآن", "count")
        for card in (self.card_down, self.card_up, self.card_total_down, self.card_total_up, self.card_count):
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
        self.filter.setPlaceholderText("بحث بالاسم أو المسار أو PID")
        self.filter.setClearButtonEnabled(True)
        tools.addWidget(self.filter, 1)

        self.btn_block = QPushButton("حظر المحدد")
        self.btn_block.setProperty("variant", "danger")
        self.btn_unblock = QPushButton("إلغاء الحظر")
        self.btn_export = QPushButton("تصدير الأسماء")
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
        title = QLabel("حركة الشبكة الإجمالية عبر الزمن")
        title.setObjectName("appTitle")
        hint = QLabel("منحنى التحميل (أزرق) والرفع (أخضر) لوحدة القياس KB/s.")
        hint.setObjectName("cardHint")
        lay.addWidget(title)
        lay.addWidget(hint)
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

    # ---------------------------------------------------------------- refresh
    def refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.engine_badge.set_state("جارٍ التحديث…")
        self._worker.request_snapshot.emit(self.include_idle)

    def _on_snapshot(self, rows: list[dict], summary: dict) -> None:
        self._busy = False
        self._last_summary = summary
        self.model.replace(rows)

        from ..util import fmt_bytes, fmt_rate

        self.card_down.set_value(fmt_rate(summary["down_bps"]), "مجموع كل التطبيقات")
        self.card_up.set_value(fmt_rate(summary["up_bps"]), "مجموع كل التطبيقات")
        self.card_total_down.set_value(fmt_bytes(summary["down_total"]), "منذ بدء الجلسة")
        self.card_total_up.set_value(fmt_bytes(summary["up_total"]), "منذ بدء الجلسة")
        self.card_count.set_value(str(summary["active"]), f"من أصل {summary['count']} عملية")

        ts = None
        self.chart_live.add_point(summary["down_bps"], summary["up_bps"], ts)
        self.chart_full.add_point(summary["down_bps"], summary["up_bps"], ts)

        ok = bool(summary.get("engine_ok"))
        self.engine_badge.set_state(
            "المحرك: " + ("ss (دقيق)" if ok else "محدود"), ok
        )
        self.settings_tab.set_engine_text(summary.get("source", "—"), ok, summary.get("error"))

        err = summary.get("error")
        msg = (
            f"{summary['active']} تطبيق نشط • {summary['count']} عملية معروضة • "
            f"التحديث كل {int(self.controller.config.get('refresh_ms', 30000))/1000:.0f} ثانية"
        )
        if err:
            msg += f" • {err}"
        self.status.showMessage(msg)
        self._update_blocked_tab()

    def _on_async_error(self, message: str) -> None:
        self._busy = False
        self.engine_badge.set_state("خطأ في الجمع", False)
        self.status.showMessage(f"تعذّر تحديث البيانات: {message}")
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
            self.status.showMessage("اختر تطبيقاً من الجدول أولاً.")
            return
        exe = row.get("exe") or ""
        if not exe:
            QMessageBox.warning(
                self,
                "تعذّر الحظر",
                "لا يمكن قراءة المسار التنفيذي لهذه العملية.\n"
                "جرّب تشغيل البرنامج مع صلاحيات أعلى أو اختر تطبيقاً يملكه مستخدمك.",
            )
            return
        name = row.get("name") or os.path.basename(exe)
        if self.controller.config.get("confirm_block", True):
            reply = QMessageBox.question(
                self,
                "تأكيد الحظر",
                f"هل تريد منع التطبيق «{name}» من الاتصال بالإنترنت؟\n\n{exe}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.status.showMessage(f"جارٍ حظر {name}… قد تظهر نافذة مصادقة النظام.")
        self._run_action(lambda: self.controller.block(exe, name), "تم حظر التطبيق بنجاح.")

    def unblock_selected(self) -> None:
        row = self._selected_row()
        if not row:
            self.status.showMessage("اختر تطبيقاً من الجدول أولاً.")
            return
        exe = row.get("exe") or ""
        if not exe:
            self.status.showMessage("مسار التنفيذ غير معروف لهذه العملية.")
            return
        self.status.showMessage(f"جارٍ إلغاء حظر {row.get('name')}…")
        self._run_action(lambda: self.controller.unblock(exe), "تم إلغاء الحظر.")

    def _unblock_slug(self, slug: str) -> None:
        self.status.showMessage("جارٍ إلغاء الحظر…")
        self._run_action(lambda: self.controller.unblock_slug(slug), "تم إلغاء الحظر.")

    def apply_blocklist(self) -> None:
        if not self.controller.blocklist.entries:
            self.status.showMessage("قائمة الحظر فارغة.")
            return
        self.status.showMessage("جارٍ إعادة تطبيق قائمة الحظر…")
        self._run_action(self.controller.apply_blocklist, "أُعيد تطبيق قائمة الحظر.")

    def _apply_blocklist_silent(self) -> None:
        if not self.controller.blocklist.entries:
            return
        self._run_action(self.controller.apply_blocklist, "", silent=True)

    def _run_action(self, fn, success_msg: str, silent: bool = False) -> None:
        self._pending_success = success_msg
        self._pending_silent = silent
        self._worker.request_action.emit(fn)

    def _on_action_done(self, ok: bool, message: str) -> None:
        success_msg = self._pending_success or "تمت العملية."
        silent = self._pending_silent
        self._pending_success = ""
        self._pending_silent = False
        if silent:
            if not ok:
                self.status.showMessage("تعذّر تطبيق قائمة الحظر تلقائياً: " + (message or "خطأ"))
            self._update_blocked_tab()
            return
        if ok:
            self.status.showMessage(success_msg)
            QMessageBox.information(self, "تمت العملية", message or success_msg)
        else:
            self.status.showMessage("فشلت العملية: " + (message or "خطأ غير معروف"))
            QMessageBox.warning(self, "فشلت العملية", message or "خطأ غير معروف")
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
            act_toggle = QAction("إلغاء حظر هذا التطبيق", self)
            act_toggle.triggered.connect(self.unblock_selected)
        else:
            act_toggle = QAction("حظر هذا التطبيق", self)
            act_toggle.triggered.connect(self.block_selected)
        menu.addAction(act_toggle)

        act_copy = QAction("نسخ المسار التنفيذي", self)
        act_copy.setEnabled(bool(row.get("exe")))
        act_copy.triggered.connect(lambda: self._copy_path(row.get("exe") or ""))
        menu.addAction(act_copy)

        menu.addSeparator()
        act_export = QAction("تصدير أسماء البرامج…", self)
        act_export.triggered.connect(self.export_names)
        menu.addAction(act_export)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_path(self, path: str) -> None:
        if not path:
            return
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(path)
        self.status.showMessage("تم نسخ المسار.")

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
            self.status.showMessage("لا توجد أسماء لتصديرها.")
            return
        default = str(Path.home() / "Desktop" / "أسماء_البرامج.txt")
        path, _ = QFileDialog.getSaveFileName(self, "حفظ أسماء البرامج", default, "ملف نصي (*.txt)")
        if not path:
            return
        try:
            Path(path).write_text("، ".join(names), encoding="utf-8")
            self.status.showMessage(f"تم التصدير إلى {path} ({len(names)} اسماً).")
        except OSError as exc:
            QMessageBox.warning(self, "فشل التصدير", str(exc))

    def _export_blocklist(self) -> None:
        default = str(Path.home() / "blocklist-backup.json")
        path, _ = QFileDialog.getSaveFileName(self, "تصدير قائمة الحظر", default, "JSON (*.json)")
        if not path:
            return
        try:
            self.controller.blocklist.export_to(Path(path))
            self.status.showMessage("تم تصدير قائمة الحظر.")
        except OSError as exc:
            QMessageBox.warning(self, "فشل التصدير", str(exc))

    def _import_blocklist(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "استيراد قائمة الحظر", str(Path.home()), "JSON (*.json)")
        if not path:
            return
        try:
            count = self.controller.blocklist.import_from(Path(path))
            self._update_blocked_tab()
            QMessageBox.information(self, "تم الاستيراد", f"تم استيراد {count} إدخالاً. اضغط «تطبيق الآن» لتفعيلها.")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "فشل الاستيراد", str(exc))

    # ---------------------------------------------------------------- settings
    def _reset_totals(self) -> None:
        reply = QMessageBox.question(
            self,
            "تصفير الإجماليات",
            "هل تريد تصفير كل الإجماليات المحفوظة؟ لا يمكن التراجع.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.controller.reset_totals()
            self.chart_live.clear()
            self.chart_full.clear()
            self.status.showMessage("تم تصفير الإجماليات.")
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
        ss_state = "متوفر" if ss else "غير متوفر"
        nft_state = "متوفر" if nft else "غير متوفر"
        cg_state = "متوفر" if cgroup2 else "غير متوفر"
        return (
            f"Python {platform.python_version()} • Qt {QtCore.qVersion()} • "
            f"ss: {ss_state} • nft: {nft_state} • cgroup v2: {cg_state}"
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
