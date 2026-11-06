from __future__ import annotations

"""Headless background collector for monthly and daily usage.

The systemd user service runs ``network-monitor --collector``.  It never
imports Qt: it scans ``/proc`` and the netlink/``ss`` socket counters, groups
bytes by the same stable application keys as the GUI, and writes them to the
shared SQLite database while holding the single-writer lock.
"""

import argparse
import signal
import sys
import threading
import time
import traceback

from . import __version__
from .collector_status import write_collector_status
from .collectors.net_conn import app_key_for, pid_cgroup
from .collectors.proc_scanner import ProcScanner
from .collectors.traffic import SampleResult, TrafficEngine
from .config import ConfigStore
from .usage import UsageStore

DEFAULT_INTERVAL_MS = 5000
GENERIC_NAMES = {"", "bwrap", "flatpak", "flatpak-session-helper", "xdg-dbus-proxy"}


def aggregate_sample(sample: SampleResult, procs: dict) -> list[dict]:
    """Aggregate a traffic sample by stable application key.

    ``sample.down_bytes``/``up_bytes`` are keyed by PID.  Background collection
    must use application keys instead, otherwise Flatpak/Snap launches would be
    split across many rows in the usage database.
    """
    buckets: dict[str, dict] = {}
    for pid in sample.active_pids:
        down = int(sample.down_bytes.get(pid, 0) or 0)
        up = int(sample.up_bytes.get(pid, 0) or 0)
        if down <= 0 and up <= 0:
            continue
        proc = procs.get(pid)
        net = sample.counters.get(pid)
        name = (
            net.name
            if net is not None and net.name
            else (getattr(proc, "name", "") or f"PID {pid}")
        )
        exe = getattr(proc, "exe", "") or ""
        cmdline = getattr(proc, "cmdline", "") or ""
        cgroup = pid_cgroup(pid) if proc is not None else ""
        app_key, display = app_key_for(exe, cgroup, cmdline)
        if not app_key:
            continue
        if display and str(name).lower() in GENERIC_NAMES:
            name = display
        bucket = buckets.get(app_key)
        if bucket is None:
            bucket = {
                "app_key": app_key,
                "name": name or "",
                "exe": exe,
                "down": 0,
                "up": 0,
            }
            buckets[app_key] = bucket
        elif not bucket.get("exe") and exe:
            bucket["exe"] = exe
        if not bucket.get("name") and name:
            bucket["name"] = name
        bucket["down"] += down
        bucket["up"] += up
    return list(buckets.values())


class Collector:
    def __init__(
        self,
        store: UsageStore,
        interval_ms: int = DEFAULT_INTERVAL_MS,
    ) -> None:
        self.store = store
        self.interval_ms = max(1000, min(60000, int(interval_ms)))
        self.config = ConfigStore()
        self.scanner = ProcScanner()
        self.traffic = TrafficEngine()
        self._last_prune = 0.0

    def _prune(self) -> None:
        try:
            months = int(self.config.get("usage_retention_months", 24))
            days = int(self.config.get("usage_retention_days", 90))
        except (TypeError, ValueError):
            months, days = 24, 90
        self.store.prune(months=months, days=days)
        self._last_prune = time.time()

    def collect_once(self) -> dict:
        """Take one sample and persist new usage.  Returns status details."""
        sample = self.traffic.poll()
        now_wall = time.time()
        keep_usage = bool(self.config.get("keep_usage", True))
        written = 0
        if sample.dt > 0 and keep_usage:
            procs = {proc.pid: proc for proc in self.scanner.scan()}
            start_wall = now_wall - sample.dt
            for row in aggregate_sample(sample, procs):
                self.store.add_interval(
                    row["app_key"],
                    row["name"],
                    row["exe"],
                    row["down"],
                    row["up"],
                    start_wall,
                    now_wall,
                )
                written += 1
        if time.time() - self._last_prune > 86400:
            self._prune()
        return {
            "source": self.traffic.describe(),
            "error": sample.error,
            "written": written,
            "engine_ok": sample.source in ("netlink", "ss"),
        }

    def run(self, stop: threading.Event | None = None) -> int:
        stop = stop or threading.Event()
        write_collector_status(
            "running",
            interval_ms=self.interval_ms,
            version=__version__,
            source=self.traffic.describe(),
        )
        try:
            self._prune()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            write_collector_status(
                "error",
                interval_ms=self.interval_ms,
                version=__version__,
                error=str(exc),
            )
        while not stop.is_set():
            started = time.monotonic()
            try:
                details = self.collect_once()
                write_collector_status(
                    "running",
                    interval_ms=self.interval_ms,
                    version=__version__,
                    **details,
                )
            except Exception as exc:  # noqa: BLE001
                traceback.print_exc()
                write_collector_status(
                    "error",
                    interval_ms=self.interval_ms,
                    version=__version__,
                    error=str(exc),
                )
            elapsed = time.monotonic() - started
            stop.wait(max(0.2, self.interval_ms / 1000.0 - elapsed))
        return 0


def _install_signal_handlers(stop: threading.Event) -> None:
    def handle(*_args) -> None:
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, handle)
        except (ValueError, OSError):
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Network Monitor background usage collector")
    parser.add_argument("--collector", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="sampling interval in milliseconds (default: from settings)",
    )
    parser.add_argument(
        "--wait",
        type=float,
        default=30.0,
        help="seconds to wait for the GUI to release usage writing",
    )
    args = parser.parse_args(argv)
    config = ConfigStore()
    try:
        interval_ms = int(args.interval or config.get("collector_interval_ms", DEFAULT_INTERVAL_MS))
    except (TypeError, ValueError):
        interval_ms = DEFAULT_INTERVAL_MS
    interval_ms = max(1000, min(60000, interval_ms))

    write_collector_status(
        "starting",
        interval_ms=interval_ms,
        version=__version__,
    )
    store = UsageStore(writer=False)
    if not store.acquire_writer(timeout=max(0.0, args.wait)):
        write_collector_status(
            "blocked",
            interval_ms=interval_ms,
            version=__version__,
            error="Another Network Monitor process is writing usage data",
        )
        print(
            "network-monitor collector: another process is writing usage data",
            file=sys.stderr,
            flush=True,
        )
        store.close()
        return 1

    stop = threading.Event()
    _install_signal_handlers(stop)
    collector = Collector(store, interval_ms=interval_ms)
    try:
        return collector.run(stop)
    finally:
        store.close()
        write_collector_status(
            "stopped",
            interval_ms=interval_ms,
            version=__version__,
        )


if __name__ == "__main__":
    raise SystemExit(main())
