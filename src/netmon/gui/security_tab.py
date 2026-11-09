from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..i18n import is_rtl, tr
from ..util import fmt_rate, short_path
from . import theme
from .widgets import StatCard

ALERT_COLUMNS = (
    ("severity", "security.col.severity", 92),
    ("time", "security.col.time", 82),
    ("kind", "security.col.kind", 205),
    ("name", "security.col.app", 155),
    ("pid", "security.col.pid", 68),
    ("endpoint", "security.col.endpoint", 185),
    ("exe", "security.col.exe", 300),
)

REPUTATION_COLUMNS = (
    ("ip", "security.rep.col.ip", 160),
    ("provider", "security.rep.col.provider", 110),
    ("score", "security.rep.col.score", 75),
    ("reports", "security.rep.col.reports", 80),
    ("country", "security.rep.col.country", 90),
    ("isp", "security.rep.col.isp", 190),
    ("status", "security.rep.col.status", 150),
)


def _leading() -> Qt.AlignmentFlag:
    return (Qt.AlignRight if is_rtl() else Qt.AlignLeft) | Qt.AlignVCenter


def _ltr(text: str) -> str:
    """Keep paths, IP addresses, and other LTR data readable in RTL layouts."""
    value = str(text or "")
    return f"\u202a{value}\u202c" if value and is_rtl() else value


def _severity_color(severity: str) -> str:
    if severity in ("critical", "high"):
        return theme.DANGER
    if severity == "medium":
        return theme.WARNING
    return theme.SUCCESS


class SecurityTab(QWidget):
    check_ip_requested = Signal(list)
    check_hash_requested = Signal(str, str)
    block_app_requested = Signal(str, str)
    block_ip_requested = Signal(str)
    unblock_ip_requested = Signal(str)
    clear_requested = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._report: dict = {}
        self._findings: list[dict] = []
        self._reputation: list[dict] = []
        self._external_ips: list[str] = []
        self._blocked_ips: set[str] = set()
        self._selected_key = ""
        self._scanning = False
        self._needle = ""
        self._severity = "all"
        self._last_hash_result: dict | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(0)
        self.title = QLabel()
        self.title.setObjectName("appTitle")
        self.subtitle = QLabel()
        self.subtitle.setObjectName("appSubtitle")
        self.subtitle.setWordWrap(True)
        titles.addWidget(self.title)
        titles.addWidget(self.subtitle)
        header.addLayout(titles, 1)

        self.btn_scan = QPushButton()
        self.btn_scan.setProperty("variant", "primary")
        self.btn_scan.clicked.connect(self._request_scan)
        self.btn_hash = QPushButton()
        self.btn_hash.clicked.connect(self._request_hash)
        self.btn_block_app = QPushButton()
        self.btn_block_app.setProperty("variant", "danger")
        self.btn_block_app.clicked.connect(self._request_block_app)
        self.btn_block_ip = QPushButton()
        self.btn_block_ip.clicked.connect(self._request_block_ip)
        self.btn_clear = QPushButton()
        self.btn_clear.clicked.connect(self.clear_requested.emit)
        for button in (
            self.btn_scan,
            self.btn_hash,
            self.btn_block_app,
            self.btn_block_ip,
            self.btn_clear,
        ):
            header.addWidget(button)
        root.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        self.card_high = StatCard("", "0", "", "down")
        self.card_medium = StatCard("", "0", "", "month")
        self.card_total = StatCard("", "0", "", "count")
        self.card_ips = StatCard("", "0", "", "up")
        for card in (self.card_high, self.card_medium, self.card_total, self.card_ips):
            cards.addWidget(card, 1)
        root.addLayout(cards)

        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._set_needle)
        tools.addWidget(self.search, 1)
        self.severity_filter = QComboBox()
        self.severity_filter.currentIndexChanged.connect(self._set_severity)
        tools.addWidget(self.severity_filter)
        root.addLayout(tools)

        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)

        alert_box = QWidget()
        alert_lay = QVBoxLayout(alert_box)
        alert_lay.setContentsMargins(0, 0, 0, 0)
        alert_lay.setSpacing(6)
        self.table = QTableWidget(0, len(ALERT_COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._open_context_menu)
        self.table.itemSelectionChanged.connect(self._render_details)
        header_view = self.table.horizontalHeader()
        header_view.setHighlightSections(False)
        for index, (_, _, width) in enumerate(ALERT_COLUMNS):
            self.table.setColumnWidth(index, width)
        self.table.horizontalHeader().setSectionResizeMode(
            len(ALERT_COLUMNS) - 1, QHeaderView.Stretch
        )
        alert_lay.addWidget(self.table, 1)
        self.details_label = QLabel()
        self.details_label.setObjectName("cardHint")
        self.details_label.setWordWrap(True)
        self.details_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        alert_lay.addWidget(self.details_label)
        splitter.addWidget(alert_box)

        reputation_box = QWidget()
        reputation_lay = QVBoxLayout(reputation_box)
        reputation_lay.setContentsMargins(0, 0, 0, 0)
        reputation_lay.setSpacing(6)
        self.reputation_title = QLabel()
        self.reputation_title.setObjectName("appTitle")
        reputation_lay.addWidget(self.reputation_title)
        self.reputation_table = QTableWidget(0, len(REPUTATION_COLUMNS))
        self.reputation_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.reputation_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.reputation_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reputation_table.verticalHeader().setVisible(False)
        self.reputation_table.setAlternatingRowColors(True)
        self.reputation_table.setShowGrid(False)
        self.reputation_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reputation_table.customContextMenuRequested.connect(
            self._open_reputation_menu
        )
        rep_header = self.reputation_table.horizontalHeader()
        rep_header.setHighlightSections(False)
        for index, (_, _, width) in enumerate(REPUTATION_COLUMNS):
            self.reputation_table.setColumnWidth(index, width)
        self.reputation_table.horizontalHeader().setSectionResizeMode(
            len(REPUTATION_COLUMNS) - 2, QHeaderView.Stretch
        )
        reputation_lay.addWidget(self.reputation_table, 1)
        splitter.addWidget(reputation_box)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([360, 230])
        root.addWidget(splitter, 1)

        self.hint = QLabel()
        self.hint.setObjectName("cardHint")
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

        self.status = QLabel()
        self.status.setObjectName("cardHint")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.retranslate()

    # ------------------------------------------------------------------ signals
    def _request_scan(self) -> None:
        if not self._external_ips:
            self.set_status(tr("security.status.no_ips"))
            return
        self.check_ip_requested.emit(list(self._external_ips[:50]))

    def _request_hash(self) -> None:
        finding = self._selected_finding()
        if finding is None or not finding.get("exe"):
            self.set_status(tr("security.no_selection"))
            return
        self.check_hash_requested.emit(
            str(finding.get("exe") or ""), str(finding.get("name") or "")
        )

    def _request_block_app(self) -> None:
        finding = self._selected_finding()
        if finding is None or not finding.get("exe"):
            self.set_status(tr("security.no_selection"))
            return
        self.block_app_requested.emit(
            str(finding.get("exe") or ""), str(finding.get("name") or "")
        )

    def _request_block_ip(self) -> None:
        finding = self._selected_finding()
        if finding is None or not finding.get("remote_ip"):
            self.set_status(tr("security.no_selection"))
            return
        self.block_ip_requested.emit(str(finding.get("remote_ip") or ""))

    # -------------------------------------------------------------------- report
    def update_report(self, report: dict) -> None:
        self._report = dict(report or {})
        self._findings = list(self._report.get("findings") or [])
        counts = self._report.get("counts") or {}
        self.card_high.set_value(str(int(counts.get("critical", 0)) + int(counts.get("high", 0))))
        self.card_medium.set_value(str(int(counts.get("medium", 0))))
        self.card_total.set_value(str(int(counts.get("total", len(self._findings)))))
        self._external_ips = [
            str(item.get("ip") or "")
            for item in (self._report.get("external_ips") or [])
            if item.get("ip")
        ]
        self.card_ips.set_value(str(len(self._external_ips)))
        self.btn_scan.setEnabled(bool(self._external_ips) and not self._scanning)
        self._render_alerts()
        self._update_hint()

    def set_reputation_results(self, results: list[dict]) -> None:
        self._reputation = list(results or [])
        self._render_reputation()
        self.set_status(tr("security.status.scan_done", count=len(self._reputation)))

    def set_hash_result(self, result: dict) -> None:
        self._last_hash_result = dict(result or {})
        self._render_details()
        if result.get("ok") and result.get("malicious"):
            self.set_status(
                tr(
                    "security.hash.malicious",
                    path=short_path(str(result.get("path") or ""), 72),
                    detections=int(result.get("detections") or 0),
                    total=int(result.get("total") or 0),
                )
            )
        elif result.get("ok"):
            self.set_status(
                tr("security.hash.safe", path=short_path(str(result.get("path") or ""), 72))
            )
        else:
            self.set_status(
                tr(
                    str(result.get("error_key") or "security.error.network"),
                    **dict(result.get("error_args") or {}),
                )
            )

    def set_blocked_ips(self, entries: list[dict]) -> None:
        self._blocked_ips = {str(item.get("ip") or "") for item in entries or []}
        self._render_details()

    def set_scanning(self, scanning: bool) -> None:
        self._scanning = bool(scanning)
        self.btn_scan.setEnabled(bool(self._external_ips) and not self._scanning)
        self.btn_scan.setText(
            tr("security.scanning") if self._scanning else tr("security.scan_ips")
        )

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    # ------------------------------------------------------------------- rendering
    def _set_needle(self, text: str) -> None:
        self._needle = (text or "").strip().lower()
        self._render_alerts()

    def _set_severity(self) -> None:
        self._severity = str(self.severity_filter.currentData() or "all")
        self._render_alerts()

    def _filtered_findings(self) -> list[dict]:
        result = []
        for finding in self._findings:
            severity = str(finding.get("severity") or "")
            if self._severity == "high":
                if severity not in ("high", "critical"):
                    continue
            elif self._severity != "all" and severity != self._severity:
                continue
            if self._needle:
                haystack = " ".join(
                    str(finding.get(key, ""))
                    for key in ("kind", "name", "exe", "remote_ip", "detail", "pid")
                ).lower()
                if self._needle not in haystack:
                    continue
            result.append(finding)
        return result

    def _render_alerts(self) -> None:
        findings = self._filtered_findings()
        self.table.setRowCount(0)
        for finding in findings:
            row = self.table.rowCount()
            self.table.insertRow(row)
            severity = str(finding.get("severity") or "low")
            endpoint = ""
            if finding.get("remote_ip"):
                endpoint = str(finding["remote_ip"])
                if finding.get("remote_port"):
                    endpoint += ":" + str(finding["remote_port"])
            values = (
                tr(f"security.severity.{severity}"),
                time.strftime(
                    "%H:%M:%S", time.localtime(float(finding.get("last_seen") or 0.0))
                ),
                tr(f"security.kind.{finding.get('kind', '')}"),
                str(finding.get("name") or "—"),
                str(finding.get("pid") or ""),
                _ltr(endpoint) or "—",
                _ltr(short_path(str(finding.get("exe") or ""), 80)) or "—",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 0:
                    item.setData(Qt.UserRole, finding.get("key") or "")
                    color = QColor(_severity_color(severity))
                    item.setForeground(color)
                    font = QFont()
                    font.setBold(severity in ("critical", "high"))
                    item.setFont(font)
                elif column in (1, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                elif column in (5, 6):
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(_leading())
                item.setToolTip(self._finding_details(finding))
                self.table.setItem(row, column, item)
        if self._selected_key:
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is not None and item.data(Qt.UserRole) == self._selected_key:
                    self.table.setCurrentCell(row, 0)
                    break
        self._render_details()

    def _render_reputation(self) -> None:
        self.reputation_table.setRowCount(0)
        for result in self._reputation:
            row = self.reputation_table.rowCount()
            self.reputation_table.insertRow(row)
            status = self._reputation_status(result)
            values = (
                _ltr(str(result.get("ip") or "—")),
                tr(f"security.provider.{result.get('provider', '')}"),
                str(result.get("score", 0) or 0),
                str(result.get("reports", 0) or 0),
                _ltr(str(result.get("country") or "—")),
                _ltr(str(result.get("isp") or "—")),
                status,
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (2, 3):
                    item.setTextAlignment(Qt.AlignCenter)
                elif column in (0, 1, 4, 5, 6):
                    item.setTextAlignment(_leading())
                if column == 6:
                    item.setForeground(
                        QColor(theme.DANGER if result.get("malicious") else theme.SUCCESS)
                    )
                if result.get("cached"):
                    item.setToolTip(tr("security.rep.cached"))
                self.reputation_table.setItem(row, column, item)

    def _reputation_status(self, result: dict) -> str:
        if not result.get("ok"):
            return tr(
                str(result.get("error_key") or "security.error.network"),
                **dict(result.get("error_args") or {}),
            )
        if result.get("malicious"):
            return tr("security.rep.malicious")
        return tr("security.rep.clean")

    def _finding_details(self, finding: dict) -> str:
        lines = [
            tr(f"security.kind.{finding.get('kind', '')}"),
            tr(f"security.severity.{finding.get('severity', 'low')}"),
            tr("security.details.app", name=finding.get("name") or "—", pid=finding.get("pid") or "—"),
        ]
        if finding.get("exe"):
            lines.append(tr("security.details.exe", path="\u202a" + str(finding["exe"]) + "\u202c"))
        if finding.get("remote_ip"):
            endpoint = str(finding["remote_ip"])
            if finding.get("remote_port"):
                endpoint += ":" + str(finding["remote_port"])
            lines.append(tr("security.details.endpoint", endpoint="\u202a" + endpoint + "\u202c"))
        if finding.get("kind") == "upload_spike":
            extra = finding.get("extra") or {}
            lines.append(
                tr(
                    "security.details.upload",
                    rate=fmt_rate(float(extra.get("up_bps", 0.0) or 0.0)),
                    baseline=fmt_rate(float(extra.get("baseline_bps", 0.0) or 0.0)),
                )
            )
        lines.append(
            tr(
                "security.details.seen",
                first=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(finding.get("first_seen") or 0.0))),
                last=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(finding.get("last_seen") or 0.0))),
                count=int(finding.get("count") or 1),
            )
        )
        return "\n".join(lines)

    def _render_details(self) -> None:
        finding = self._selected_finding()
        if finding is not None:
            self._selected_key = str(finding.get("key") or "")
            text = self._finding_details(finding)
            if finding.get("remote_ip"):
                if str(finding["remote_ip"]) in self._blocked_ips:
                    text += "\n" + tr("security.details.blocked_ip")
                else:
                    text += "\n" + tr("security.details.can_block_ip")
            self.details_label.setText(text)
        elif self._last_hash_result:
            self.details_label.setText(self._format_hash_details(self._last_hash_result))
        else:
            self.details_label.setText(tr("security.none"))

    def _format_hash_details(self, result: dict) -> str:
        if not result.get("ok"):
            return tr(
                str(result.get("error_key") or "security.error.network"),
                **dict(result.get("error_args") or {}),
            )
        lines = [
            tr("security.hash.title"),
            tr("security.hash.path", path="\u202a" + str(result.get("path") or "") + "\u202c"),
            tr("security.hash.sha", sha="\u202a" + str(result.get("sha256") or "") + "\u202c"),
            tr("security.provider." + str(result.get("provider") or "")),
            tr("security.hash.cached") if result.get("cached") else tr("security.hash.fresh"),
        ]
        if result.get("malicious"):
            lines.append(
                tr(
                    "security.hash.malicious",
                    path=short_path(str(result.get("path") or ""), 72),
                    detections=int(result.get("detections") or 0),
                    total=int(result.get("total") or 0),
                )
            )
        else:
            lines.append(
                tr("security.hash.safe", path=short_path(str(result.get("path") or ""), 72))
            )
        if result.get("signatures"):
            lines.append(tr("security.hash.signatures", values=", ".join(result["signatures"])))
        if result.get("tags"):
            lines.append(tr("security.hash.tags", values=", ".join(result["tags"])))
        return "\n".join(lines)

    def _update_hint(self) -> None:
        counts = self._report.get("counts") or {}
        self.hint.setText(
            tr(
                "security.hint",
                total=int(counts.get("total", len(self._findings))),
                ips=len(self._external_ips),
            )
        )

    # -------------------------------------------------------------------- context
    def _selected_finding(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item is None:
            return None
        key = item.data(Qt.UserRole)
        for finding in self._findings:
            if finding.get("key") == key:
                return finding
        return None

    def _open_context_menu(self, pos) -> None:
        index = self.table.indexAt(pos)
        if not index.isValid():
            return
        self.table.setCurrentCell(index.row(), 0)
        finding = self._selected_finding()
        if finding is None:
            return
        menu = QMenu(self)
        if finding.get("remote_ip"):
            action = QAction(tr("security.context.check_ip"), self)
            action.triggered.connect(
                lambda: self.check_ip_requested.emit([str(finding.get("remote_ip") or "")])
            )
            menu.addAction(action)
            if str(finding["remote_ip"]) in self._blocked_ips:
                action = QAction(tr("security.context.unblock_ip"), self)
                action.triggered.connect(
                    lambda: self.unblock_ip_requested.emit(str(finding.get("remote_ip") or ""))
                )
            else:
                action = QAction(tr("security.context.block_ip"), self)
                action.triggered.connect(
                    lambda: self.block_ip_requested.emit(str(finding.get("remote_ip") or ""))
                )
            menu.addAction(action)
        if finding.get("exe"):
            menu.addSeparator()
            action = QAction(tr("security.check_hash"), self)
            action.triggered.connect(
                lambda: self.check_hash_requested.emit(
                    str(finding.get("exe") or ""), str(finding.get("name") or "")
                )
            )
            menu.addAction(action)
            action = QAction(tr("security.block_app"), self)
            action.triggered.connect(
                lambda: self.block_app_requested.emit(
                    str(finding.get("exe") or ""), str(finding.get("name") or "")
                )
            )
            menu.addAction(action)
            action = QAction(tr("security.context.copy_path"), self)
            action.triggered.connect(self._copy_path)
            menu.addAction(action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _open_reputation_menu(self, pos) -> None:
        index = self.reputation_table.indexAt(pos)
        if not index.isValid():
            return
        self.reputation_table.selectRow(index.row())
        item = self.reputation_table.item(index.row(), 0)
        if item is None:
            return
        ip = item.text()
        if not ip or ip == "—":
            return
        menu = QMenu(self)
        action = QAction(tr("security.context.check_ip"), self)
        action.triggered.connect(lambda: self.check_ip_requested.emit([ip]))
        menu.addAction(action)
        if ip in self._blocked_ips:
            action = QAction(tr("security.context.unblock_ip"), self)
            action.triggered.connect(lambda: self.unblock_ip_requested.emit(ip))
        else:
            action = QAction(tr("security.context.block_ip"), self)
            action.triggered.connect(lambda: self.block_ip_requested.emit(ip))
        menu.addAction(action)
        menu.exec(self.reputation_table.viewport().mapToGlobal(pos))

    def _copy_path(self) -> None:
        finding = self._selected_finding()
        if finding is None or not finding.get("exe"):
            return
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(str(finding.get("exe") or ""))
        self.set_status(tr("security.status.copied"))

    # ------------------------------------------------------------------ translation
    def retranslate(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        self.title.setText(tr("security.title"))
        self.subtitle.setText(tr("security.subtitle"))
        self.card_high.set_title(tr("security.card.high"))
        self.card_high.set_hint(tr("security.card.hint"))
        self.card_medium.set_title(tr("security.card.medium"))
        self.card_medium.set_hint(tr("security.card.hint"))
        self.card_total.set_title(tr("security.card.total"))
        self.card_total.set_hint(tr("security.card.hint"))
        self.card_ips.set_title(tr("security.card.external"))
        self.card_ips.set_hint(tr("security.card.external_hint"))
        for card in (self.card_high, self.card_medium, self.card_total, self.card_ips):
            card.set_rtl(is_rtl())
        self.search.setPlaceholderText(tr("security.search"))
        self.btn_scan.setText(tr("security.scanning") if self._scanning else tr("security.scan_ips"))
        self.btn_hash.setText(tr("security.check_hash"))
        self.btn_block_app.setText(tr("security.block_app"))
        self.btn_block_ip.setText(tr("security.block_ip"))
        self.btn_clear.setText(tr("security.clear"))
        self.reputation_title.setText(tr("security.rep.title"))
        self.severity_filter.blockSignals(True)
        self.severity_filter.clear()
        for key, code in (
            ("security.filter.all", "all"),
            ("security.filter.high", "high"),
            ("security.filter.medium", "medium"),
            ("security.filter.low", "low"),
        ):
            self.severity_filter.addItem(tr(key), code)
        index = self.severity_filter.findData(self._severity)
        if index >= 0:
            self.severity_filter.setCurrentIndex(index)
        self.severity_filter.blockSignals(False)
        self.table.setHorizontalHeaderLabels([tr(key) for _, key, _ in ALERT_COLUMNS])
        self.reputation_table.setHorizontalHeaderLabels(
            [tr(key) for _, key, _ in REPUTATION_COLUMNS]
        )
        self.details_label.setAlignment(_leading())
        self.hint.setAlignment(_leading())
        self.status.setAlignment(_leading())
        self._render_alerts()
        self._render_reputation()
        self._render_details()
        self._update_hint()

    def apply_theme(self) -> None:
        self._render_alerts()
        self._render_reputation()
        self.table.viewport().update()
        self.reputation_table.viewport().update()
