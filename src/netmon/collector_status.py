from __future__ import annotations

"""Shared status file for the optional background usage collector.

The GUI and the systemd user service live in different processes, so they use
one small JSON file instead of a socket.  A status is only considered live
when it says ``running`` and its heartbeat is recent enough for the configured
collection interval.
"""

import json
import os
import time
from pathlib import Path

from .config import COLLECTOR_STATUS_FILE


def write_collector_status(
    state: str,
    path: Path = COLLECTOR_STATUS_FILE,
    **fields,
) -> None:
    payload = {
        "state": str(state),
        "updated": time.time(),
        "pid": os.getpid(),
        **fields,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        # Status reporting must never take the collector down.
        pass


def read_collector_status(path: Path = COLLECTOR_STATUS_FILE) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError, TypeError):
        return {
            "state": "unknown",
            "updated": 0.0,
            "running": False,
            "stale": True,
        }
    if not isinstance(payload, dict):
        return {
            "state": "unknown",
            "updated": 0.0,
            "running": False,
            "stale": True,
        }
    try:
        updated = float(payload.get("updated", 0.0))
    except (TypeError, ValueError):
        updated = 0.0
    try:
        interval_ms = int(payload.get("interval_ms", 5000))
    except (TypeError, ValueError):
        interval_ms = 5000
    max_age = max(15.0, (max(1000, interval_ms) / 1000.0) * 3.0 + 10.0)
    age = max(0.0, time.time() - updated)
    running = str(payload.get("state")) == "running" and age <= max_age
    payload["updated"] = updated
    payload["running"] = running
    payload["stale"] = not running
    payload["age"] = age
    return payload
