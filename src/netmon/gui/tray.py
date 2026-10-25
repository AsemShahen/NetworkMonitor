from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..i18n import tr
from .icons import get_app_icon


class Tray(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(get_app_icon(), parent)
        self._parent = parent
        self.setToolTip(tr("app.title"))
        self.menu = QMenu(parent)
        self.show_action = QAction(parent)
        self.show_action.triggered.connect(parent.showNormal)
        self.show_action.triggered.connect(parent.activateWindow)
        self.menu.addAction(self.show_action)
        self.quit_action = QAction(parent)
        self.quit_action.triggered.connect(parent.close)
        self.menu.addAction(self.quit_action)
        self.setContextMenu(self.menu)
        self.retranslate()
        try:
            self.activated.connect(lambda r: parent.showNormal() if r == QSystemTrayIcon.Trigger else None)
        except Exception:
            pass

    def retranslate(self) -> None:
        self.setToolTip(tr("app.title"))
        self.show_action.setText(tr("tray.show"))
        self.quit_action.setText(tr("tray.quit"))
