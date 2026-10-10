from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

def run_pkexec(*args) -> tuple[int, str, str]:
    """تشغيل أمر عبر pkexec في نظام لينكس."""
    try:
        p = subprocess.run(["pkexec"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return -1, "", str(e)


def has_pkexec() -> bool:
    return Path("/usr/bin/pkexec").exists() or Path("/bin/pkexec").exists()


def has_polkit_agent() -> bool:
    return bool(os.environ.get("PKEXEC_UID") or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))