from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path.home() / ".local/share/glasswire"
LOG_DIR = Path.home() / ".cache/glasswire/logs"
PID_DIR = Path.home() / ".cache/glasswire/run"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
PID_DIR.mkdir(parents=True, exist_ok=True)