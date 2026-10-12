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
            # skip kernel/system threads heuristics
            exe = (p.exe or '').lower()
            name = (p.name or '').lower()
            cmd = (p.cmdline or '').lower()
            # kernel has no exe or starts with /proc? usually exe empty for many kthreads
            if not exe and p.pid < 1000:
                continue  # skip most kernel/init
            if name.startswith('kworker') or name.startswith('rcu') or name.startswith('ksoftirqd') or name in ('kthreadd','systemd-journal','systemd-udevd'):
                # show minimal? prefer user apps; skip pure kernel
                continue
            rx = random.randint(100000, 8000000)
            tx = random.randint(50000, 2000000)
            lrx = self._last_rx.get(p.pid,0); ltx = self._last_tx.get(p.pid,0); lts = self._last_ts.get(p.pid,0)
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
