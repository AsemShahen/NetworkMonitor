from __future__ import annotations

import os, time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableView, QPushButton, QStatusBar, QMenu, QSystemTrayIcon, QLineEdit, QComboBox
)

from .theme import THEME
from .traffic_table import TrafficTable, TrafficModel


def fmt_bps(v):
    v = max(0, float(v))
    if v >= 1024*1024:
        return f"{v/(1024*1024):0.2f} MB/s"
    return f"{v/1024:0.1f} KB/s"


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
        self.btn_refresh = QPushButton("تحديث الآن")
        self.btn_block = QPushButton("حظر المحدد")
        self.btn_unblock = QPushButton("إلغاء حظر المحدد")
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("بحث بالاسم أو المسار...")
        top.addWidget(self.btn_refresh)
        top.addWidget(self.btn_block)
        top.addWidget(self.btn_unblock)
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
        self.timer.start(30000)
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_block.clicked.connect(self.block_selected)
        self.btn_unblock.clicked.connect(self.unblock_selected)

    def refresh(self):
        procs = self.ctx.proc_scan()
        rows = []
        for p in procs[:100]:
            # p may be dict or object
            name = p.get("name") if isinstance(p, dict) else getattr(p, "name", "")
            pid = p.get("pid") if isinstance(p, dict) else getattr(p, "pid", 0)
            exe = p.get("exe") if isinstance(p, dict) else getattr(p, "exe", "")
            down_bps = p.get("down_bps") if isinstance(p, dict) else getattr(p, "down_bps", 0.0)
            up_bps = p.get("up_bps") if isinstance(p, dict) else getattr(p, "up_bps", 0.0)
            down_total = p.get("down_total") if isinstance(p, dict) else getattr(p, "down_total", 0)
            up_total = p.get("up_total") if isinstance(p, dict) else getattr(p, "up_total", 0)
            blocked = p.get("blocked") if isinstance(p, dict) else getattr(p, "blocked", False)
            rows.append({
                "name": name,
                "pid": pid,
                "exe": exe,
                "down_bps": fmt_bps(down_bps),
                "up_bps": fmt_bps(up_bps),
                "down_total": down_total,
                "up_total": up_total,
                "blocked": blocked,
            })
        self.model.replace(rows)
        self.status.showMessage(f"جاهز | {len(procs)} عملية | تحديث كل 1 ثانية")
# replace tray init

    def get_selected_exe(self):
        idx = self.table.selectionModel().currentIndex()
        if not idx.isValid():
            return None
        row = idx.row()
        if 0 <= row < len(self.model.rows):
            return self.model.rows[row].get("exe", "")
        return None

    def block_selected(self):
        exe = self.get_selected_exe()
        if not exe:
            self.status.showMessage("اختر عملية أولاً ثم اضغط حظر")
            return
        self.ctx.blocklist.add(self.ctx.blocklist.__class__.__name__)  # dummy
        # actually add
        from ..config import BlockEntry, slugify
        import time
        self.ctx.add_block(exe)
        self.status.showMessage(f"تمت إضافة {exe} إلى قائمة الحظر")
        self.refresh()

    def unblock_selected(self):
        exe = self.get_selected_exe()
        if not exe:
            self.status.showMessage("اختر عملية أولاً ثم اضغط إلغاء الحظر")
            return
        self.ctx.remove_block(exe)
        self.status.showMessage(f"تم إلغاء حظر {exe}")
        self.refresh()
