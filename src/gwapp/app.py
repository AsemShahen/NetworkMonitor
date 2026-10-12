from __future__ import annotations

import sys, os
from PySide6.QtWidgets import QApplication

from .collectors.proc_scanner import ProcScanner
from .gui.main_window import MainWindow


from .controller import Engine
from .config import BlocklistStore, BlockEntry, slugify
import os, time
class Context:
    def __init__(self):
        self.engine = Engine()
        self.blocklist = BlocklistStore()

    def proc_scan(self):
        rows = self.engine.sample()[:200]
        slugs = {slugify(r.get("exe","")) for r in rows}
        # mark blocked
        blocked = set(self.blocklist.entries.keys())
        for r in rows:
            r["blocked"] = slugify(r.get("exe","")) in blocked
        return rows

    def add_block(self, exe: str):
        if not exe: return False
        from .firewall.helper_client import HelperClient
        hc = HelperClient()
        ok = hc.block(exe)
        ent = BlockEntry(exe=exe, slug=slugify(exe), name=os.path.basename(exe), when=time.time())
        self.blocklist.add(ent)
        return ok or True

    def remove_block(self, exe: str):
        if not exe: return False
        from .firewall.helper_client import HelperClient
        hc = HelperClient()
        ok = hc.unblock(exe)
        self.blocklist.remove(slugify(exe))
        return ok or True


def run():
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    app = QApplication(sys.argv)
    ctx = Context()
    w = MainWindow(ctx)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
