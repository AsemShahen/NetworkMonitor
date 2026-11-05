from __future__ import annotations

import time
from datetime import datetime

import pyqtgraph as pg
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from ..i18n import is_rtl, tr
from ..util import fmt_bytes
from . import theme
from .widgets import StatCard

COLUMNS = [
    ("name", "usage.col.app", 260),
    ("down", "usage.col.down", 120),
    ("up", "usage.col.up", 120),
    ("total", "usage.col.total", 130),
    ("share", "usage.col.share", 100),
    ("last_seen", "usage.col.last_seen", 160),
]

SORT_ROLE = Qt.UserRole + 1


def _leading() -> Qt.AlignmentFlag:
    return (Qt.AlignRight if is_rtl() else Qt.AlignLeft) | Qt.AlignVCenter


class UsageModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self.grand_total = 0

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal and 0 <= section < len(COLUMNS):
            return tr(COLUMNS[section][1])
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        key = COLUMNS[index.column()][0]
        total = int(row.get("total", 0))

        if role == SORT_ROLE:
            if key in ("down", "up", "total", "share", "last_seen"):
                return row.get(key, 0)
            return str(row.get(key, ""))

        if role == Qt.DisplayRole:
            if key == "name":
                return str(row.get("name") or row.get("app_key") or "—")
            if key in ("down", "up", "total"):
                return "\u202a" + fmt_bytes(row.get(key, 0)) + "\u202c"
            if key == "share":
                share = (100.0 * total / self.grand_total) if self.grand_total else 0.0
                return f"{share:.1f}%"
            if key == "last_seen":
                ts = float(row.get("last_seen", 0) or 0)
                if ts <= 0:
                    return "—"
                return "\u202a" + time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) + "\u202c"
            return str(row.get(key, ""))

        if role == Qt.ForegroundRole:
            if key == "down":
                return QColor(theme.DOWN)
            if key == "up":
                return QColor(theme.UP)
            if key == "total":
                return QColor(theme.TEXT)
            if key in ("share", "last_seen"):
                return QColor(theme.MUTED)

        if role == Qt.TextAlignmentRole:
            if key in ("down", "up", "total", "share", "last_seen"):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(_leading())

        if role == Qt.ToolTipRole:
            return tr(
                "usage.tooltip",
                app=row.get("app_key", ""),
                exe=row.get("exe", ""),
            )
        return None

    def replace(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self.rows = list(rows)
        self.grand_total = sum(int(r.get("total", 0)) for r in self.rows)
        self.endResetModel()

    def retranslate(self) -> None:
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(COLUMNS) - 1)
        if self.rows:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self.rows) - 1, len(COLUMNS) - 1),
            )


class UsageFilterProxy(QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self._needle = ""
        self.setSortRole(SORT_ROLE)

    def set_needle(self, text: str) -> None:
        self._needle = (text or "").strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model: UsageModel = self.sourceModel()  # type: ignore[assignment]
        if model is None or source_row >= len(model.rows):
            return False
        if not self._needle:
            return True
        row = model.rows[source_row]
        hay = " ".join(
            str(row.get(key, "")) for key in ("name", "app_key", "exe")
        ).lower()
        return self._needle in hay


class UsageTable(QTableView):
    def __init__(self) -> None:
        super().__init__()
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self.horizontalHeader().setHighlightSections(False)
        self.horizontalHeader().setStretchLastSection(False)

    def apply_column_widths(self) -> None:
        for i, (_, _, width) in enumerate(COLUMNS):
            self.setColumnWidth(i, width)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


class UsageChart(QWidget):
    """Daily download/upload chart for the selected month."""

    def __init__(self, parent=None):
        super().__init__(parent)
        axis = pg.DateAxisItem(orientation="bottom")
        self.plot = pg.PlotWidget(axisItems={"bottom": axis})
        self.plot.setBackground(theme.SURFACE)
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.setLabel("left", "GB", color=theme.MUTED)
        self.plot.getAxis("left").enableAutoSIPrefix(False)
        self.plot.getAxis("left").setPen(pg.mkPen(theme.BORDER))
        self.plot.getAxis("bottom").setPen(pg.mkPen(theme.BORDER))
        self.plot.getAxis("left").setTextPen(pg.mkPen(theme.MUTED))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen(theme.MUTED))

        down_brush = QColor(theme.DOWN)
        down_brush.setAlpha(38)
        up_brush = QColor(theme.UP)
        up_brush.setAlpha(30)
        self.curve_down = self.plot.plot(
            [], [],
            pen=pg.mkPen(theme.DOWN, width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(theme.DOWN),
            fillLevel=0,
            brush=pg.mkBrush(down_brush),
            name=tr("usage.chart.down"),
        )
        self.curve_up = self.plot.plot(
            [], [],
            pen=pg.mkPen(theme.UP, width=2),
            symbol="o",
            symbolSize=4,
            symbolBrush=pg.mkBrush(theme.UP),
            fillLevel=0,
            brush=pg.mkBrush(up_brush),
            name=tr("usage.chart.up"),
        )
        self.legend = self.plot.addLegend(offset=(-10, 10))
        self.apply_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.plot)
        now = time.time()
        self.plot.setYRange(0, 1, padding=0)
        self.plot.setXRange(now - 86400, now, padding=0)

    def apply_theme(self) -> None:
        self.plot.setBackground(theme.SURFACE)
        self.plot.setLabel("left", "GB", color=theme.MUTED)
        for axis in (self.plot.getAxis("left"), self.plot.getAxis("bottom")):
            axis.setPen(pg.mkPen(theme.BORDER))
            axis.setTextPen(pg.mkPen(theme.MUTED))
        self.curve_down.setPen(pg.mkPen(theme.DOWN, width=2))
        self.curve_down.setSymbolBrush(pg.mkBrush(theme.DOWN))
        down_brush = QColor(theme.DOWN)
        down_brush.setAlpha(38)
        self.curve_down.setBrush(pg.mkBrush(down_brush))
        self.curve_up.setPen(pg.mkPen(theme.UP, width=2))
        self.curve_up.setSymbolBrush(pg.mkBrush(theme.UP))
        up_brush = QColor(theme.UP)
        up_brush.setAlpha(30)
        self.curve_up.setBrush(pg.mkBrush(up_brush))
        self.legend.setLabelTextColor(theme.TEXT)

    def set_data(self, daily: list[dict]) -> None:
        if not daily:
            self.clear()
            return
        xs: list[float] = []
        down: list[float] = []
        up: list[float] = []
        for row in daily:
            try:
                ts = datetime.strptime(str(row["day"]), "%Y-%m-%d").timestamp()
            except (KeyError, ValueError):
                continue
            xs.append(ts)
            down.append(max(0, int(row.get("down", 0))) / 1024 ** 3)
            up.append(max(0, int(row.get("up", 0))) / 1024 ** 3)
        if not xs:
            self.clear()
            return
        self.curve_down.setData(xs, down)
        self.curve_up.setData(xs, up)
        peak = max(max(down, default=0.0), max(up, default=0.0), 0.05)
        self.plot.setYRange(0, peak * 1.25, padding=0)
        self.plot.setXRange(xs[0] - 43200, xs[-1] + 43200, padding=0)

    def retranslate(self) -> None:
        self.legend.clear()
        self.legend.addItem(self.curve_down, tr("usage.chart.down"))
        self.legend.addItem(self.curve_up, tr("usage.chart.up"))

    def clear(self) -> None:
        now = time.time()
        self.plot.setYRange(0, 1, padding=0)
        self.plot.setXRange(now - 86400, now, padding=0)
        self.curve_down.setData([], [])
        self.curve_up.setData([], [])


class UsageTab(QWidget):
    export_requested = Signal(str)
    reset_requested = Signal(str)

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._month = ""
        self._rows: list[dict] = []
        self._daily: list[dict] = []
        self._totals = (0, 0)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        self.title = QLabel()
        self.title.setObjectName("appTitle")
        header.addWidget(self.title)
        header.addStretch(1)
        self.month = QComboBox()
        self.month.setMinimumWidth(150)
        self.month.currentIndexChanged.connect(self._on_month_changed)
        header.addWidget(self.month)
        self.export_btn = QPushButton()
        self.export_btn.clicked.connect(self._emit_export)
        header.addWidget(self.export_btn)
        self.reset_btn = QPushButton()
        self.reset_btn.setProperty("variant", "danger")
        self.reset_btn.clicked.connect(self._emit_reset)
        header.addWidget(self.reset_btn)
        outer.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.card_down = StatCard("", "0 B", "", "down")
        self.card_up = StatCard("", "0 B", "", "up")
        self.card_total = StatCard("", "0 B", "", "total-down")
        for card in (self.card_down, self.card_up, self.card_total):
            cards.addWidget(card, 1)
        outer.addLayout(cards)

        self.chart = UsageChart()
        self.chart.setMinimumHeight(180)
        outer.addWidget(self.chart, 2)

        tools = QHBoxLayout()
        tools.setSpacing(8)
        self.filter = QLineEdit()
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(lambda text: self.proxy.set_needle(text))
        tools.addWidget(self.filter, 1)
        outer.addLayout(tools)

        self.model = UsageModel()
        self.proxy = UsageFilterProxy()
        self.proxy.setSourceModel(self.model)
        self.table = UsageTable()
        self.table.setModel(self.proxy)
        self.table.apply_column_widths()
        self.table.sortByColumn(3, Qt.DescendingOrder)
        outer.addWidget(self.table, 3)

        self.hint = QLabel()
        self.hint.setObjectName("cardHint")
        self.hint.setWordWrap(True)
        outer.addWidget(self.hint)

        self.refresh_months()
        self.retranslate()

    def _current_month(self) -> str:
        return datetime.now().strftime("%Y-%m")

    def refresh_months(self) -> None:
        previous = self.month.currentData() if self.month.count() else self._month
        months = self.controller.usage_months()
        current = self._current_month()
        if current not in months:
            months.insert(0, current)
        self.month.blockSignals(True)
        self.month.clear()
        for month in months:
            label = month
            if month == current:
                label = f"{month}  ({tr('usage.current')})"
            self.month.addItem(label, month)
        idx = self.month.findData(previous) if previous else -1
        if idx < 0:
            idx = self.month.findData(current)
        self.month.setCurrentIndex(max(0, idx))
        self.month.blockSignals(False)

    def _on_month_changed(self) -> None:
        self.refresh()

    def refresh(self) -> None:
        month = str(self.month.currentData() or self._current_month())
        self._month = month
        self._rows = self.controller.usage_month(month)
        self._daily = self.controller.usage_daily(month)
        self._totals = self.controller.usage_totals(month)
        self.model.replace(self._rows)
        self.chart.set_data(self._daily)
        down, up = self._totals
        self.card_down.set_value(fmt_bytes(down), tr("usage.card.hint"))
        self.card_up.set_value(fmt_bytes(up), tr("usage.card.hint"))
        self.card_total.set_value(
            fmt_bytes(down + up),
            tr("usage.card.total_hint", down=fmt_bytes(down), up=fmt_bytes(up)),
        )
        self.reset_btn.setEnabled(bool(self._rows))
        self.hint.setText(tr("usage.note", count=len(self._rows)))

    def _emit_export(self) -> None:
        self.export_requested.emit(self._month or self._current_month())

    def _emit_reset(self) -> None:
        self.reset_requested.emit(self._month or self._current_month())

    def apply_theme(self) -> None:
        self.chart.apply_theme()
        self.table.viewport().update()

    def retranslate(self) -> None:
        self.title.setText(tr("tab.usage"))
        self.export_btn.setText(tr("usage.export"))
        self.reset_btn.setText(tr("usage.reset"))
        self.filter.setPlaceholderText(tr("usage.search"))
        self.card_down.set_title(tr("usage.card.down"))
        self.card_up.set_title(tr("usage.card.up"))
        self.card_total.set_title(tr("usage.card.total"))
        self.card_down.set_hint(tr("usage.card.hint"))
        self.card_up.set_hint(tr("usage.card.hint"))
        self.card_total.set_hint(tr("usage.card.hint"))
        self.model.retranslate()
        self.chart.retranslate()
        self.refresh_months()
        self.refresh()
        self._apply_direction()

    def _apply_direction(self) -> None:
        rtl = is_rtl()
        self.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        align = _leading()
        self.title.setAlignment(align)
        self.hint.setAlignment(align)
        self.card_down.set_rtl(rtl)
        self.card_up.set_rtl(rtl)
        self.card_total.set_rtl(rtl)
