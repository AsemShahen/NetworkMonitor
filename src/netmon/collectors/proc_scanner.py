from __future__ import annotations

import os
import time
from pathlib import Path

from ..models import ProcInfo
from ..util import pretty_name

PAGE_SIZE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, PermissionError):
        return ""


def _read_comm(pid: int) -> str:
    return _read_text(f"/proc/{pid}/comm").strip()


def _read_exe(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/exe")
    except OSError:
        return ""


def _read_cmdline(pid: int) -> str:
    raw = _read_text(f"/proc/{pid}/cmdline")
    return raw.replace("\x00", " ").strip()


def _read_uid(pid: int) -> int:
    for line in _read_text(f"/proc/{pid}/status").splitlines():
        if line.startswith("Uid:"):
            parts = line.split()
            if len(parts) > 1:
                try:
                    return int(parts[1])
                except ValueError:
                    return -1
    return -1


def _read_state(pid: int) -> str:
    for line in _read_text(f"/proc/{pid}/status").splitlines():
        if line.startswith("State:"):
            parts = line.split()
            if len(parts) > 1:
                return parts[1]
    return "?"


def _read_cpu_rss(pid: int) -> tuple[int, int]:
    """يرجع (utime+stime بالـ jiffies، rss بالبايت) من /proc/<pid>/stat."""
    raw = _read_text(f"/proc/{pid}/stat")
    if not raw:
        return 0, 0
    try:
        rparen = raw.rfind(")")
        rest = raw[rparen + 2:].split()
        utime = int(rest[11])
        stime = int(rest[12])
        rss_pages = int(rest[21])
        return utime + stime, rss_pages * PAGE_SIZE
    except (IndexError, ValueError):
        return 0, 0


def _read_cpu_total() -> int:
    """إجمالي jiffies لكل الأنوية من /proc/stat."""
    raw = _read_text("/proc/stat")
    for line in raw.splitlines():
        if line.startswith("cpu "):
            try:
                return sum(int(x) for x in line.split()[1:])
            except ValueError:
                return 0
    return 0


class ProcScanner:
    """ماسح العمليات من /proc مع حساب نسبة CPU بين عينتين متتاليتين."""

    def __init__(self) -> None:
        self._prev_proc: dict[int, tuple[int, float]] = {}
        self._prev_total: int = 0
        self._prev_ts: float = 0.0

    def scan(self) -> list[ProcInfo]:
        now = time.monotonic()
        total_now = _read_cpu_total()
        total_delta = total_now - self._prev_total if self._prev_total else 0
        dt = now - self._prev_ts if self._prev_ts else 0.0

        procs: list[ProcInfo] = []
        new_prev: dict[int, tuple[int, float]] = {}

        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            pid = int(entry)
            try:
                comm = _read_comm(pid)
                if not comm:
                    continue
                exe = _read_exe(pid)
                cmdline = _read_cmdline(pid)
                cpu_jiffies, rss = _read_cpu_rss(pid)

                if total_delta > 0 and pid in self._prev_proc:
                    prev_jiffies, _ = self._prev_proc[pid]
                    delta = max(0, cpu_jiffies - prev_jiffies)
                    cores = os.cpu_count() or 1
                    cpu_pct = 100.0 * cores * delta / total_delta
                elif total_delta > 0 and self._prev_total:
                    cpu_pct = 0.0
                else:
                    cpu_pct = 0.0

                new_prev[pid] = (cpu_jiffies, now)

                procs.append(
                    ProcInfo(
                        pid=pid,
                        name=pretty_name(comm, exe, cmdline),
                        exe=exe,
                        cmdline=cmdline,
                        uid=_read_uid(pid),
                        state=_read_state(pid),
                        cpu=round(cpu_pct, 1),
                        rss=rss,
                    )
                )
            except (OSError, ValueError):
                continue

        self._prev_proc = new_prev
        self._prev_total = total_now
        self._prev_ts = now
        return procs
