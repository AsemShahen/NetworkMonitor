from __future__ import annotations
import random, time
from typing import Dict

class DemoCollector:
    def __init__(self):
        self._last = time.time()
        self._last_tx = 10000
        self._last_rx = 20000

    def poll(self):
        now = time.time()
        dt = now - self._last
        self._last = now
        # fake
        base_rx = 10_000_000 + random.randint(-1_000_000, 5_000_000)
        base_tx = 5_000_000 + random.randint(-500_000, 2_000_000)
        rx_bps = max(0, (base_rx - self._last_rx)) / dt if dt > 0 else 0
        tx_bps = max(0, (base_tx - self._last_tx)) / dt if dt > 0 else 0
        self._last_rx = base_rx; self._last_tx = base_tx
        return {"pid": {}, "demo": {"down": rx_bps, "up": tx_bps}}
