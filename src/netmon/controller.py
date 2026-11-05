from __future__ import annotations

import os
import time
from datetime import datetime

from .collectors.net_conn import app_key_for, pid_cgroup
from .collectors.proc_scanner import ProcScanner
from .collectors.traffic import TrafficEngine
from .config import BlocklistStore, ConfigStore, TotalsStore, slugify
from .i18n import tr
from .models import BlockEntry
from .usage import UsageStore


class Controller:
    """تنسيق بين ماسح العمليات، محرك الشبكة، الإعدادات وقائمة الحظر."""

    def __init__(self) -> None:
        self.scanner = ProcScanner()
        self.traffic = TrafficEngine()
        self.config = ConfigStore()
        self.blocklist = BlocklistStore()
        self.totals = TotalsStore()
        self.usage = UsageStore()
        self._last_totals_save = time.time()
        self._last_usage_prune = time.time()
        self._recent: dict[str, float] = {}
        self.session_down = 0
        self.session_up = 0
        self.last_error: str | None = None
        self._prune_usage()

    def _prune_usage(self) -> None:
        try:
            months = int(self.config.get("usage_retention_months", 24))
            days = int(self.config.get("usage_retention_days", 90))
        except (TypeError, ValueError):
            months, days = 24, 90
        self.usage.prune(months=months, days=days)

    # ---------- الرصد ----------
    def snapshot(self, include_idle: bool = False) -> tuple[list[dict], dict]:
        now_wall = time.time()
        procs = {p.pid: p for p in self.scanner.scan()}
        sample = self.traffic.poll()
        start_wall = now_wall - sample.dt if sample.dt > 0 else now_wall

        rows: list[dict] = []
        seen: set[int] = set()
        group_cgroups = bool(self.config.get("group_cgroups", True))
        recent_seconds = self._recent_seconds()

        for pid in sample.active_pids:
            p = procs.get(pid)
            nc = sample.counters.get(pid)
            name = nc.name if nc and nc.name else (p.name if p else f"PID {pid}")
            exe = p.exe if p else ""
            cmdline = p.cmdline if p else ""
            cgroup = pid_cgroup(pid) if p else ""
            app_key, app_display = app_key_for(exe, cgroup, cmdline)
            row = self._row(pid, name, exe, cmdline, p, nc, sample, active=True)
            self._decorate(row, app_key, app_display, cgroup, pid, group_cgroups)
            rows.append(row)
            seen.add(pid)

        # Always inspect idle processes so recently-active applications remain
        # visible for a short grace period even when show_idle is off.
        for pid, p in procs.items():
            if pid in seen:
                continue
            if p.uid < 1000 and not p.exe:
                continue
            cgroup = pid_cgroup(pid)
            app_key, app_display = app_key_for(p.exe, cgroup, p.cmdline)
            recent_key = self._recent_key(app_key, pid, group_cgroups)
            if not include_idle and not self._is_recent(recent_key, recent_seconds):
                continue
            row = self._row(pid, p.name, p.exe, p.cmdline, p, None, sample, active=False)
            self._decorate(row, app_key, app_display, cgroup, pid, group_cgroups)
            rows.append(row)

        # Record usage/totals once per process row, before display grouping.
        keep_usage = bool(self.config.get("keep_usage", True))
        for row in rows:
            down = int(row.pop("_down_bytes", 0))
            up = int(row.pop("_up_bytes", 0))
            exe = row.get("exe") or ""
            if down or up:
                if keep_usage and row.get("app_key"):
                    self.usage.add_interval(
                        row["app_key"],
                        row.get("name") or "",
                        exe,
                        down,
                        up,
                        start_wall,
                        now_wall,
                    )
                if exe:
                    self.totals.add(exe, down, up)
                self.session_down += down
                self.session_up += up
            if exe:
                d, u = self.totals.get(exe)
                row["down_total"] = d
                row["up_total"] = u
                row["_exe_totals"] = {exe: (d, u)}
            else:
                row["down_total"] = 0
                row["up_total"] = 0
                row["_exe_totals"] = {}
            if row.get("active"):
                self._recent[row["recent_key"]] = now_wall

        # Keep recent-activity entries bounded.
        if recent_seconds > 0:
            cutoff = now_wall - max(60, recent_seconds * 2)
            for key, ts in list(self._recent.items()):
                if ts < cutoff:
                    del self._recent[key]
        else:
            self._recent.clear()

        if group_cgroups:
            rows = self._group_rows(rows)
        else:
            for row in rows:
                row["pids"] = [row["pid"]]
                row["process_count"] = 1

        if self.config.get("keep_totals", True):
            if time.time() - self._last_totals_save > 30:
                self.totals.save()
                self._last_totals_save = time.time()
        if time.time() - self._last_usage_prune > 86400:
            self._prune_usage()
            self._last_usage_prune = time.time()

        rows.sort(key=lambda r: (r["down_bps"] + r["up_bps"], r["cpu"]), reverse=True)

        total_down_bps = sum(r["down_bps"] for r in rows)
        total_up_bps = sum(r["up_bps"] for r in rows)
        month_key = datetime.now().strftime("%Y-%m")
        month_down, month_up = self.usage.month_totals(month_key)
        summary = {
            "down_bps": total_down_bps,
            "up_bps": total_up_bps,
            "down_total": self.session_down,
            "up_total": self.session_up,
            "count": len(rows),
            "processes": sum(int(r.get("process_count", 1)) for r in rows),
            "active": sum(1 for r in rows if r["active"]),
            "source": self.traffic.describe(),
            "engine_ok": self.traffic.available,
            "error": sample.error,
            "blocked_count": len(self.blocklist.entries),
            "diagnostics": sample.diagnostics,
            "month_key": month_key,
            "month_down": month_down,
            "month_up": month_up,
            "grouped": group_cgroups,
        }
        return rows, summary

    def _recent_seconds(self) -> int:
        try:
            return max(0, int(self.config.get("recent_seconds", 300)))
        except (TypeError, ValueError):
            return 300

    @staticmethod
    def _recent_key(app_key: str, pid: int, group_cgroups: bool) -> str:
        if group_cgroups and app_key.startswith(("flatpak:", "snap:", "appimage:")):
            return app_key
        return f"pid:{pid}"

    def _is_recent(self, key: str, seconds: int) -> bool:
        if seconds <= 0:
            return False
        last = self._recent.get(key)
        return last is not None and (time.time() - last) <= seconds

    @staticmethod
    def _decorate(
        row: dict,
        app_key: str,
        app_display: str,
        cgroup: str,
        pid: int,
        group_cgroups: bool,
    ) -> None:
        generic = {"", "bwrap", "flatpak", "flatpak-session-helper", "xdg-dbus-proxy"}
        if app_display and str(row.get("name") or "").lower() in generic:
            row["name"] = app_display
        row["app_key"] = app_key
        row["app_display"] = app_display
        row["cgroup"] = cgroup
        row["recent_key"] = Controller._recent_key(app_key, pid, group_cgroups)
        row["group_key"] = row["recent_key"]
        row["pids"] = [pid]
        row["process_count"] = 1

    def _row(self, pid, name, exe, cmdline, p, nc, sample, active: bool) -> dict:
        slug = slugify(exe) if exe else ""
        unmeasured = int(nc.unmeasured_udp) if nc else 0
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
            "tcp_sockets": (nc.tcp_sockets if nc else 0),
            "udp_sockets": (nc.udp_sockets if nc else 0),
            "udp_unmeasured": unmeasured,
            "has_unmeasured": bool(unmeasured),
            "blocked": bool(slug and self.blocklist.has(slug)),
            "active": active,
            "idle": not active,
            "_down_bytes": int(getattr(sample, "down_bytes", {}).get(pid, 0)),
            "_up_bytes": int(getattr(sample, "up_bytes", {}).get(pid, 0)),
            "_exe_totals": {},
        }

    def _group_rows(self, rows: list[dict]) -> list[dict]:
        grouped: dict[str, dict] = {}
        for row in rows:
            key = row.get("group_key") or f"pid:{row['pid']}"
            if not key.startswith(("flatpak:", "snap:", "appimage:")):
                grouped[f"pid:{row['pid']}"] = row
                continue
            current = grouped.get(key)
            if current is None:
                grouped[key] = row
                continue
            self._merge_row(current, row)
        return list(grouped.values())

    @staticmethod
    def _merge_row(target: dict, row: dict) -> None:
        target_pids = target.setdefault("pids", [target["pid"]])
        for pid in row.get("pids", [row["pid"]]):
            if pid not in target_pids:
                target_pids.append(pid)
        target["process_count"] = len(target_pids)
        previous_target_rate = target.get("down_bps", 0.0) + target.get("up_bps", 0.0)
        target["down_bps"] += row.get("down_bps", 0.0)
        target["up_bps"] += row.get("up_bps", 0.0)
        target["conns"] += int(row.get("conns", 0))
        target["tcp_sockets"] += int(row.get("tcp_sockets", 0))
        target["udp_sockets"] += int(row.get("udp_sockets", 0))
        target["udp_unmeasured"] += int(row.get("udp_unmeasured", 0))
        target["has_unmeasured"] = bool(
            target.get("has_unmeasured") or row.get("has_unmeasured")
        )
        target["active"] = bool(target.get("active") or row.get("active"))
        target["idle"] = not target["active"]
        target["blocked"] = bool(target.get("blocked") or row.get("blocked"))

        # Keep the busiest process as the representative row for blocking and
        # for the executable path shown in the table.
        row_rate = row.get("down_bps", 0.0) + row.get("up_bps", 0.0)
        if row_rate > previous_target_rate:
            for key in ("pid", "name", "exe", "cmdline", "uid", "state", "cpu", "rss"):
                if key in row:
                    target[key] = row[key]

        totals = target.setdefault("_exe_totals", {})
        totals.update(row.get("_exe_totals", {}))
        target["down_total"] = sum(value[0] for value in totals.values())
        target["up_total"] = sum(value[1] for value in totals.values())

    # ---------- الحظر ----------
    def block(self, exe: str, name: str = "") -> tuple[bool, str]:
        if not exe:
            return False, tr("error.no_exe")
        from .firewall.helper_client import HelperClient

        ok, err = HelperClient().block(exe, name)
        if ok:
            entry = BlockEntry(exe=exe, slug=slugify(exe), name=name or os.path.basename(exe), when=time.time())
            self.blocklist.add(entry)
        return ok, err

    def unblock(self, exe: str) -> tuple[bool, str]:
        if not exe:
            return False, tr("error.no_exe_short")
        from .firewall.helper_client import HelperClient

        ok, err = HelperClient().unblock(exe)
        if ok:
            self.blocklist.remove(slugify(exe))
        return ok, err

    def unblock_slug(self, slug: str) -> tuple[bool, str]:
        entry = self.blocklist.entries.get(slug)
        if not entry:
            return False, tr("error.not_in_blocklist")
        return self.unblock(entry.exe)

    def apply_blocklist(self) -> tuple[bool, str]:
        entries = [e.to_dict() for e in self.blocklist.list()]
        if not entries:
            return True, tr("action.blocklist_empty")
        from .firewall.helper_client import HelperClient

        return HelperClient().apply(entries)

    # ---------- الإعدادات ----------
    def set_refresh_ms(self, ms: int) -> None:
        self.config.set("refresh_ms", int(ms))

    def reset_totals(self) -> None:
        self.totals.reset()
        self.session_down = self.session_up = 0
        self._last_totals_save = time.time()

    # ---------- الاستهلاك الشهري ----------
    def usage_months(self) -> list[str]:
        return self.usage.months()

    def usage_month(self, month: str) -> list[dict]:
        return self.usage.monthly(month)

    def usage_daily(self, month: str) -> list[dict]:
        return self.usage.daily(month)

    def usage_totals(self, month: str) -> tuple[int, int]:
        return self.usage.month_totals(month)

    def reset_usage_month(self, month: str) -> None:
        self.usage.reset_month(month)

    def export_usage(self, path, month: str) -> int:
        return self.usage.export_csv(path, month)

    def shutdown(self) -> None:
        try:
            self.totals.save()
            self.config.save()
            self.usage.close()
        except Exception:
            pass
