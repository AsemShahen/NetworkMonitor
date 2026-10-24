from __future__ import annotations

import os
import time

from .config import BlocklistStore, ConfigStore, TotalsStore, slugify
from .collectors.proc_scanner import ProcScanner
from .collectors.traffic import TrafficEngine
from .models import BlockEntry


class Controller:
    """تنسيق بين ماسح العمليات، محرك الشبكة، الإعدادات وقائمة الحظر."""

    def __init__(self) -> None:
        self.scanner = ProcScanner()
        self.traffic = TrafficEngine()
        self.config = ConfigStore()
        self.blocklist = BlocklistStore()
        self.totals = TotalsStore()
        self._last_totals_save = time.time()
        self.session_down = 0
        self.session_up = 0
        self.last_error: str | None = None

    # ---------- الرصد ----------
    def snapshot(self, include_idle: bool = False) -> tuple[list[dict], dict]:
        procs = {p.pid: p for p in self.scanner.scan()}
        sample = self.traffic.poll()

        rows: list[dict] = []
        seen: set[int] = set()

        for pid in sample.active_pids:
            p = procs.get(pid)
            nc = sample.counters.get(pid)
            name = (nc.name if nc and nc.name else (p.name if p else f"PID {pid}"))
            exe = p.exe if p else ""
            cmdline = p.cmdline if p else ""
            rows.append(self._row(pid, name, exe, cmdline, p, nc, sample, active=True))
            seen.add(pid)

        if include_idle:
            for pid, p in procs.items():
                if pid in seen:
                    continue
                if p.uid < 1000 and not p.exe:
                    continue
                rows.append(self._row(pid, p.name, p.exe, p.cmdline, p, None, sample, active=False))

        # تجميع الإجماليات
        for r in rows:
            exe = r["exe"]
            down = int(r.pop("_down_bytes"))
            up = int(r.pop("_up_bytes"))
            if exe:
                self.totals.add(exe, down, up)
                d, u = self.totals.get(exe)
                r["down_total"] = d
                r["up_total"] = u
            else:
                r["down_total"] = r["down_total"] + 0
                r["up_total"] = r["up_total"] + 0
            self.session_down += down
            self.session_up += up

        if self.config.get("keep_totals", True):
            if time.time() - self._last_totals_save > 30:
                self.totals.save()
                self._last_totals_save = time.time()

        rows.sort(key=lambda r: (r["down_bps"] + r["up_bps"], r["cpu"]), reverse=True)

        total_down_bps = sum(r["down_bps"] for r in rows)
        total_up_bps = sum(r["up_bps"] for r in rows)
        summary = {
            "down_bps": total_down_bps,
            "up_bps": total_up_bps,
            "down_total": self.session_down,
            "up_total": self.session_up,
            "count": len(rows),
            "active": sum(1 for r in rows if r["active"]),
            "source": self.traffic.describe(),
            "engine_ok": self.traffic.available,
            "error": sample.error,
            "blocked_count": len(self.blocklist.entries),
        }
        return rows, summary

    def _row(self, pid, name, exe, cmdline, p, nc, sample, active: bool) -> dict:
        slug = slugify(exe) if exe else ""
        return {
            "pid": pid,
            "name": name,
            "exe": exe or "",
            "cmdline": cmdline or "",
            "uid": (p.uid if p else -1),
            "state": (p.state if p else "?"),
            "cpu": (p.cpu if p else 0.0),
            "rss": (p.rss if p else 0),
            "down_bps": float(getattr(sample, "down_bps", {}).get(pid, 0.0)),
            "up_bps": float(getattr(sample, "up_bps", {}).get(pid, 0.0)),
            "down_total": 0,
            "up_total": 0,
            "conns": (nc.sockets if nc else 0),
            "blocked": bool(slug and self.blocklist.has(slug)),
            "active": active,
            "idle": not active,
            "_down_bytes": int(getattr(sample, "down_bytes", {}).get(pid, 0)),
            "_up_bytes": int(getattr(sample, "up_bytes", {}).get(pid, 0)),
        }

    # ---------- الحظر ----------
    def block(self, exe: str, name: str = "") -> tuple[bool, str]:
        if not exe:
            return False, "لا يمكن تحديد المسار التنفيذي لهذه العملية (صلاحيات غير كافية)."
        from .firewall.helper_client import HelperClient

        ok, err = HelperClient().block(exe, name)
        if ok:
            entry = BlockEntry(exe=exe, slug=slugify(exe), name=name or os.path.basename(exe), when=time.time())
            self.blocklist.add(entry)
        return ok, err

    def unblock(self, exe: str) -> tuple[bool, str]:
        if not exe:
            return False, "مسار التنفيذ غير معروف."
        from .firewall.helper_client import HelperClient

        ok, err = HelperClient().unblock(exe)
        if ok:
            self.blocklist.remove(slugify(exe))
        return ok, err

    def unblock_slug(self, slug: str) -> tuple[bool, str]:
        entry = self.blocklist.entries.get(slug)
        if not entry:
            return False, "هذا التطبيق غير موجود في قائمة الحظر."
        return self.unblock(entry.exe)

    def apply_blocklist(self) -> tuple[bool, str]:
        entries = [e.to_dict() for e in self.blocklist.list()]
        if not entries:
            return True, "قائمة الحظر فارغة."
        from .firewall.helper_client import HelperClient

        return HelperClient().apply(entries)

    # ---------- الإعدادات ----------
    def set_refresh_ms(self, ms: int) -> None:
        self.config.set("refresh_ms", int(ms))

    def reset_totals(self) -> None:
        self.totals.reset()
        self.session_down = self.session_up = 0
        self._last_totals_save = time.time()

    def shutdown(self) -> None:
        try:
            self.totals.save()
            self.config.save()
        except Exception:
            pass
