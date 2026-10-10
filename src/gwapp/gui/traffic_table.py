from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView

COL_NAMES = ["الاسم", "PID", "المسار", "تحميل/s", "رفع/s", "تحميل إجمالي", "رفع إجمالي", "حالة"]


class TrafficModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.rows: list[dict] = []

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COL_NAMES)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            keys = ["name", "pid", "exe", "down_bps", "up_bps", "down_total", "up_total", "blocked"]
            k = keys[col]
            v = row.get(k, "")
            if k == "blocked":
                return "محظور" if v else "مسموح"
            return v
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return COL_NAMES[section]
        return None

    def replace(self, rows: list[dict]) -> None:
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()


class TrafficTable(QTableView):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSortingEnabled(True)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)
        self.verticalHeader().setVisible(False)
        self.resizeColumnsToContents()
