from __future__ import annotations
import os
from PySide6.QtGui import QIcon
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"

def get_app_icon():
    icon_path = ICONS_DIR / "network-monitor.png"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()
