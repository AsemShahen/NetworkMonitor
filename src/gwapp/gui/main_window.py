from __future__ import annotations

import os, time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableView, QPushButton, QStatusBar, QMenu, QSystemTrayIcon, QLineEdit, QComboBox
)

from .theme import THEME
from .traffic_table import TrafficTable, TrafficModel


class MainWindow(QMainWindow):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("مراقب الشبكة | GlassWire-like")
        self.setMinimumSize(1100, 720)
        self.apply_theme()
        self._build()
        self._start()

    def apply_theme(self):
        self.setStyleSheet(THEME)

    def _build(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # tab 1
        self.tab_net = QWidget()
        self.tabs.addTab(self.tab_net, "رصد الشبكة")
        lay = QVBoxLayout(self.tab_net)
        top = QHBoxLayout()
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("بحث بالاسم أو المسار...")
        self.engine_box = QComboBox()
        self.engine_box.addItems(["تلقائي (المساعد أولاً)", "المساعد المميز (pkexec)", "صلاحيات المستخدم فقط", "وضع تجريبي"])
        top.addWidget(QLabel("محرك الرصد:"))
        top.addWidget(self.engine_box)
        top.addWidget(self.filter)
        lay.addLayout(top)

        self.model = TrafficModel()
        self.table = TrafficTable()
        self.table.setModel(self.model)
        lay.addWidget(self.table)

        # status
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("جاهز | التحميل الكلي: 0 B | الرفع الكلي: 0 B")

        # tray
        from .tray import Tray
        self.tray = Tray(self)
        try:
            self.tray.show()
        except Exception:
            pass

    def _start(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def refresh(self):
        procs = self.ctx.proc_scan()
        rows = []
        dsum = usum = 0
        for p in procs[:100]:
            rows.append({
                "name": p.name,
                "pid": p.pid,
                "exe": p.exe,
                "down_bps": f"{p.down_bps:0.1f}",
                "up_bps": f"{p.up_bps:0.1f}",
                "down_total": p.down_total,
                "up_total": p.up_total,
                "blocked": p.blocked,
            })
        self.model.replace(rows)
        self.status.showMessage(f"جاهز | {len(procs)} عملية | تحديث كل 1 ثانية")
# replace tray init
