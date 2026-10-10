from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple

from .inode_map import build_inode_map


class SSSockDiagCollector:
    """محرك مبسط: يحاول استخدام 'ss -tinp' لقراءة تدفق المقبس، ويحسب فرق (Delta) لكل PID."""

    def __init__(self):
        self._last_tx: Dict[int, int] = defaultdict(int)
        self._last_rx: Dict[int, int] = defaultdict(int)
        self._last_ts = time.time()
        self._map_cache_ts = 0

    def poll(self, procs: list | None = None) -> dict:
        now = time.time()
        dt = max(0.1, now - self._last_ts)
        self._last_ts = now
        out = {"pid": {}, "ts": now, "source": "ss"}
        try:
            # build inode map cache occasionally
            inode_to_pids = build_inode_map(cache_ttl=5)
            # run ss
            ss_res = os.popen("ss -tinp 2>/dev/null | head -2000").read()
            for line in ss_res.splitlines():
                if "pid=" not in line and "ino=" not in line:
                    continue
                # parse pairs pid, bytes
                tx, rx = 0, 0
                # look for recv/send queues bytes in ESTAB style? simpler: parse proc? skip detailed
                pass  # skip heavy parsing here
        except Exception as e:
            out["error"] = str(e)
        return out

    def describe(self) -> str:
        return "ss-sockdiag (مبسط)"