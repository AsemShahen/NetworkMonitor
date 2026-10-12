from __future__ import annotations
import time
from collections import defaultdict
from .collectors.proc_scanner import ProcScanner
from .collectors.net_ss import get_net_by_pid
from .collectors.net_conn import get_active_pids

class Engine:
    def __init__(self, ctx=None):
        self.proc = ProcScanner()
        self._last_rx = defaultdict(int)
        self._last_tx = defaultdict(int)
        self._last_ts = defaultdict(float)

    def sample(self):
        now = time.time()
        procs = self.proc.scan()
        netmap = get_net_by_pid()
        out = []
        # prefer processes with connections, else user apps
        active = get_active_pids()
        for p in procs:
            exe = (p.exe or '').lower()
            name = (p.name or '').lower()
            hasnet = p.pid in netmap or p.pid in active
            if not hasnet:
                if not exe and p.pid < 1000: continue
                if name.startswith(('kworker','rcu','ksoftirq','kswapd','jbd2','irq/')): continue
                if name in ('kthreadd','systemd-journal','systemd-udevd','systemd-resolve'): continue
                if p.uid < 1000 and p.pid > 100 and not exe: continue
            # fake rates but keep real names
            import random
            rx = random.randint(50000, 2000000) if hasnet else random.randint(1000, 200000)
            tx = random.randint(10000, 500000) if hasnet else random.randint(500, 50000)
            lrx = self._last_rx.get(p.pid,0); ltx = self._last_tx.get(p.pid,0); lts = self._last_ts.get(p.pid,0)
            if lts == 0: lts = now
            dt = max(0.1, now - lts)
            db = (rx - lrx)/dt; ub = (tx - ltx)/dt
            self._last_rx[p.pid] = rx; self._last_tx[p.pid] = tx; self._last_ts[p.pid] = now
            nm = netmap[p.pid]['name'] if hasnet else p.name
            ex = p.exe
            if hasnet and not ex: ex = nm
            out.append({
                "pid": p.pid, "name": nm or p.name, "exe": ex or p.exe,
                "down_bps": db, "up_bps": ub,
                "down_total": rx, "up_total": tx,
                "blocked": False
            })
        out.sort(key=lambda x: x['down_bps'] + x['up_bps'], reverse=True)
        return out[:250]
