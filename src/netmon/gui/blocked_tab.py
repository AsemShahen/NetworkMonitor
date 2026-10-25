from __future__ import annotations

import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config import BLOCKLIST_FILE
from ..i18n import is_rtl, tr


class BlockedTab(QWidget):
    unblock_requested = Signal(str)
    export_requested = Signal()
    import_requested = Signal()
    apply_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries = []
        self._slugs: list[str] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        self.title = QLabel()
        self.title.setObjectName("appTitle")
        header.addWidget(self.title)
        header.addStretch(1)

        self.btn_apply = QPushButton()
        self.btn_apply.setProperty("variant", "primary")
        self.btn_apply.clicked.connect(self.apply_requested.emit)
        self.btn_unblock = QPushButton()
        self.btn_unblock.setProperty("variant", "danger")
        self.btn_unblock.clicked.connect(self._emit_unblock)
        self.btn_export = QPushButton()
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.btn_import = QPushButton()
        self.btn_import.clicked.connect(self.import_requested.emit)

        header.addWidget(self.btn_apply)
        header.addWidget(self.btn_unblock)
        header.addWidget(self.btn_export)
        header.addWidget(self.btn_import)
        root.addLayout(header)

        self.hint = QLabel()
        self.hint.setObjectName("cardHint")
        self.hint.setWordWrap(True)
        root.addWidget(self.hint)

        self.table = QTableWidget(0, 4)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        root.addWidget(self.table, 1)

        self.retranslate()

    def set_entries(self, entries) -> None:
        self._entries = list(entries)
        self._render()

    def _render(self) -> None:
        self._slugs = [e.slug for e in self._entries]
        self.table.setRowCount(0)
        align_text = (Qt.AlignRight if is_rtl() else Qt.AlignLeft) | Qt.AlignVCenter
        for entry in self._entries:
            row = self.table.rowCount()
            self.table.insertRow(row)
            when = (
                "\u202a" + time.strftime("%Y-%m-%d %H:%M", time.localtime(entry.when)) + "\u202c"
                if entry.when else "—"
            )
            exe_text = ("\u202a" + entry.exe + "\u202c") if entry.exe else "—"
            values = [entry.name or "—", exe_text, when, entry.slug]
            for col, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter if col in (2, 3) else align_text)
                self.table.setItem(row, col, item)
        if self._entries:
            self.hint.setText(
                tr("blocked.count", count=len(self._entries), path="\u202a" + str(BLOCKLIST_FILE) + "\u202c")
            )
        else:
            self.hint.setText(tr("blocked.empty"))

    def retranslate(self) -> None:
        self.setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        self.title.setText(tr("blocked.title"))
        self.btn_apply.setText(tr("blocked.apply"))
        self.btn_unblock.setText(tr("blocked.unblock"))
        self.btn_export.setText(tr("blocked.export"))
        self.btn_import.setText(tr("blocked.import"))
        self.table.setHorizontalHeaderLabels([
            tr("blocked.col.app"),
            tr("blocked.col.exe"),
            tr("blocked.col.when"),
            tr("blocked.col.slug"),
        ])
        self.hint.setAlignment((Qt.AlignRight if is_rtl() else Qt.AlignLeft) | Qt.AlignVCenter)
        self._render()

    def selected_slug(self) -> str | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._slugs):
            return self._slugs[row]
        return None

    def _emit_unblock(self) -> None:
        slug = self.selected_slug()
        if slug:
            self.unblock_requested.emit(slug)
