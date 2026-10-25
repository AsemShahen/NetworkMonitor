from __future__ import annotations

import signal
import sys

from PySide6.QtWidgets import QApplication

from .controller import Controller
from .gui.icons import get_app_icon
from .gui.language import apply_language
from .gui.main_window import MainWindow
from .i18n import set_language, tr


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("network-monitor")
    app.setOrganizationName("Network Monitor")
    app.setDesktopFileName("network-monitor")
    app.setStyle("Fusion")
    app.setWindowIcon(get_app_icon())

    controller = Controller()
    set_language(str(controller.config.get("language", "en")))
    app.setApplicationDisplayName(tr("app.title"))
    apply_language(app)

    window = MainWindow(controller)
    window.show()
    app.aboutToQuit.connect(window.shutdown)

    # إنهاء نظيف عند إشارات النظام
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    signal.signal(signal.SIGTERM, lambda *_: app.quit())

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
