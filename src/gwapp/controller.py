from __future__ import annotations
import time
from collections import defaultdict
from .collectors.proc_scanner import ProcScanner

class Engine:
    def __init__(self, ctx=None):
        self.proc = ProcScanner()
        self._last_rx = defaultdict(int)
        self._last_tx = defaultdict(int)
        self._last_ts = defaultdict(float)

    def sample(self):
        now = time.time()
        procs = self.proc.scan()[:150]
        # demo network per proc
        import random
        out = []
        for p in procs:
            rx = random.randint(100000, 8000000)
            tx = random.randint(50000, 2000000)
            lrx = self._last_rx[p.pid]; ltx = self._last_tx[p.pid]; lts = self._last_ts[p.pid]
            if lts == 0: lts = now
            dt = max(0.1, now - lts)
            db = (rx - lrx)/dt; ub = (tx - ltx)/dt
            self._last_rx[p.pid] = rx; self._last_tx[p.pid] = tx; self._last_ts[p.pid] = now
            out.append({
                "pid": p.pid, "name": p.name, "exe": p.exe,
                "down_bps": db, "up_bps": ub,
                "down_total": rx, "up_total": tx,
                "blocked": False
            })
        return out
