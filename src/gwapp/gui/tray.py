from __future__ import annotations
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from .icons import get_app_icon

class Tray(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(get_app_icon(), parent)
        self.setToolTip("مراقب الشبكة")
        menu = QMenu(parent)
        show = QAction("إظهار", parent)
        show.triggered.connect(parent.showNormal)
        show.triggered.connect(parent.activateWindow)
        menu.addAction(show)
        quit = QAction("خروج", parent)
        quit.triggered.connect(parent.close)
        menu.addAction(quit)
        self.setContextMenu(menu)
        try:
            self.activated.connect(lambda r: parent.showNormal() if r == QSystemTrayIcon.Trigger else None)
        except Exception:
            pass
