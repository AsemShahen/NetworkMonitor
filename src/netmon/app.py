from __future__ import annotations

import signal
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from .controller import Controller
from .gui.icons import get_app_icon
from .gui.main_window import MainWindow


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("network-monitor")
    app.setApplicationDisplayName("Network Monitor")
    app.setOrganizationName("Network Monitor")
    app.setDesktopFileName("network-monitor")
    app.setStyle("Fusion")
    app.setLayoutDirection(Qt.RightToLeft)
    app.setFont(QFont("Noto Sans Arabic UI", 10))
    app.setWindowIcon(get_app_icon())

    controller = Controller()
    window = MainWindow(controller)
    window.show()
    app.aboutToQuit.connect(window.shutdown)

    # إنهاء نظيف عند إشارات النظام
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
