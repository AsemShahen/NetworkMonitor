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


class BlockedTab(QWidget):
    unblock_requested = Signal(str)
    export_requested = Signal()
    import_requested = Signal()
    apply_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("التطبيقات المحظورة من الإنترنت")
        title.setObjectName("appTitle")
        header.addWidget(title)
        header.addStretch(1)

        self.btn_apply = QPushButton("تطبيق الآن")
        self.btn_apply.setProperty("variant", "primary")
        self.btn_apply.clicked.connect(self.apply_requested.emit)
        self.btn_unblock = QPushButton("إلغاء حظر المحدد")
        self.btn_unblock.setProperty("variant", "danger")
        self.btn_unblock.clicked.connect(self._emit_unblock)
        self.btn_export = QPushButton("تصدير القائمة")
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.btn_import = QPushButton("استيراد القائمة")
        self.btn_import.clicked.connect(self.import_requested.emit)

        header.addWidget(self.btn_apply)
        header.addWidget(self.btn_unblock)
        header.addWidget(self.btn_export)
        header.addWidget(self.btn_import)
        root.addLayout(header)

        self.hint = QLabel("قائمة الحظر تُحفظ تلقائياً. لإعادة تطبيقها بعد إعادة تشغيل الجهاز اضغط «تطبيق الآن».")
        self.hint.setObjectName("cardHint")
        root.addWidget(self.hint)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["التطبيق", "المسار التنفيذي", "تاريخ الإضافة", "المعرّف"])
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

        self._slugs: list[str] = []

    def set_entries(self, entries) -> None:
        self._slugs = [e.slug for e in entries]
        self.table.setRowCount(0)
        for entry in entries:
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
                if col in (2, 3):
                    item.setTextAlignment(Qt.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row, col, item)
        self.hint.setText(
            f"{len(entries)} تطبيق محظور. القائمة تُحفظ في ~/.local/share/network-monitor/blocklist.json"
            if entries
            else "لا توجد تطبيقات محظورة حالياً."
        )

    def selected_slug(self) -> str | None:
        row = self.table.currentRow()
        if 0 <= row < len(self._slugs):
            return self._slugs[row]
        return None

    def _emit_unblock(self) -> None:
        slug = self.selected_slug()
        if slug:
            self.unblock_requested.emit(slug)
