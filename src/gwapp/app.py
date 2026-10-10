from __future__ import annotations

import sys, os
from PySide6.QtWidgets import QApplication

from .collectors.proc_scanner import ProcScanner
from .gui.main_window import MainWindow


from .controller import Engine
class Context:
    def __init__(self):
        self.engine = Engine()

    def proc_scan(self):
        return self.engine.sample()[:200]


def run():
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    app = QApplication(sys.argv)
    ctx = Context()
    w = MainWindow(ctx)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
