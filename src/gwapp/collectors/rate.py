from __future__ import annotations
from collections import defaultdict
import time

class RateMeter:
    def __init__(self):
        self._last_rx = defaultdict(int)
        self._last_tx = defaultdict(int)
        self._last_ts = defaultdict(float)

    def update(self, pid: int, rx: int, tx: int, now: float) -> tuple[float, float]:
        last_rx = self._last_rx.get(pid, 0)
        last_tx = self._last_tx.get(pid, 0)
        last_ts = self._last_ts.get(pid, now)
        dt = max(0.001, now - last_ts)
        self._last_rx[pid] = rx
        self._last_tx[pid] = tx
        self._last_ts[pid] = now
        return (rx - last_rx) / dt, (tx - last_tx) / dt  # bytes/s
