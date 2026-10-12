from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict

from ..models import ProcInfo


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def _read_cmdline(pid: int) -> str:
    return _read_text(Path(f"/proc/{pid}/cmdline")).replace("\0", " ")


def _read_exe(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/exe")
    except Exception:
        return ""


def _read_comm(pid: int) -> str:
    return _read_text(Path(f"/proc/{pid}/comm"))


def _read_status(pid: int) -> dict:
    d = {}
    for line in _read_text(Path(f"/proc/{pid}/status")).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def _read_stat(pid: int) -> tuple[float, int]:
    # utime + stime in jiffies, rss in pages; simplified
    try:
        s = _read_text(Path(f"/proc/{pid}/stat"))
        parts = re.split(r"\s+", s, maxsplit=52)
        utime = int(parts[13]) if len(parts) > 13 else 0
        stime = int(parts[14]) if len(parts) > 14 else 0
        start = int(parts[21]) if len(parts) > 21 else 0
        rss = int(parts[23]) if len(parts) > 23 else 0
        cpu_total = utime + stime
        return float(cpu_total), rss
    except Exception:
        return 0.0, 0


class ProcScanner:
    """ماسح عمليات لينكس من /proc."""

    def __init__(self):
        self._cache: Dict[int, tuple[float, float]] = {}

    def scan(self) -> list[ProcInfo]:
        procs: list[ProcInfo] = []
        now = time.time()
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue
            pid = int(pid_str)
            try:
                comm = _read_comm(pid)
                exe = _read_exe(pid)
                cmdline = _read_cmdline(pid)
                name = comm or (Path(exe).name if exe else '')
                if not name or len(name) < 3:
                    name = Path(exe).name or ''
                low = (name + ' ' + cmdline).lower()
                if 'waterfox' in low or 'firefox' in low or 'librewolf' in low:
                    name = 'Waterfox' if 'waterfox' in low else ('LibreWolf' if 'librewolf' in low else 'Firefox')
                    if not exe:
                        exe = cmdline.split()[0] if cmdline else exe
                status = _read_status(pid)
                cpu_total, rss = _read_stat(pid)
                uid = 0
                try:
                    uid_str = status.get("Uid", "0\t0").split()[0]
                    uid = int(uid_str)
                except Exception:
                    pass
                low = (comm + ' ' + cmdline + ' ' + exe).lower()
                name_res = name if 'name' in locals() else (comm or (Path(exe).name if exe else ''))
                # detect real browser binary
                if ('waterfox' in exe.lower() or 'firefox' in exe.lower() or 'librewolf' in exe.lower() or 'brave' in exe.lower() or 'opera' in exe.lower() or 'chromium' in exe.lower() or 'chrome' in exe.lower()):
                    b = exe.lower()
                    if 'waterfox' in b: name_res = 'Waterfox'
                    elif 'brave' in b: name_res = 'Brave'
                    elif 'librewolf' in b: name_res = 'LibreWolf'
                    elif 'opera' in b: name_res = 'Opera'
                    elif 'chromium' in b: name_res = 'Chromium'
                    elif 'chrome' in b: name_res = 'Chrome'
                    elif 'firefox' in b: name_res = 'Firefox'
                elif ('waterfox' in low or 'firefox' in low or 'librewolf' in low or 'brave' in low or 'opera' in low):
                    # avoid shell commands
                    if cmdline and ('bash' in cmdline.split()[0] or 'sh' in cmdline.split()[0] or 'python' in cmdline.split()[0]):
                        pass  # skip shell wrapper
                    else:
                        if 'waterfox' in low: name_res = 'Waterfox'
                        elif 'brave' in low: name_res = 'Brave'
                        elif 'librewolf' in low: name_res = 'LibreWolf'
                        elif 'opera' in low: name_res = 'Opera'
                        else: name_res = 'Firefox'
                if not exe and cmdline:
                    exe = cmdline.split()[0]
                p = ProcInfo(
                    pid=pid,
                    name=name_res,
                    exe=exe,
                    cmdline=cmdline,
                    uid=uid,
                    state=status.get("State", "?").split()[0] if status.get("State") else "?",
                    cpu=cpu_total / 100.0,
                    rss=rss,
                    down_bps=0.0,
                    up_bps=0.0,
                )
                procs.append(p)
            except Exception:
                continue
        return procs

    def filter_user(self, procs: list[ProcInfo]) -> list[ProcInfo]:
        # keep all in testing/sandbox; in system keep uid >=1000 or same user
        return procs