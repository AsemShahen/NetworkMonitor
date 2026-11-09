from __future__ import annotations

"""Local, API-free security heuristics.

The analyzer consumes the rows and socket records already produced by the
traffic engine.  It never starts a network request and never touches the
filesystem beyond cheap path checks, so it can run on every refresh.
"""

import ipaddress
import os
import time
from collections import OrderedDict, defaultdict, deque

from .models import SEVERITY_ORDER, SecurityFinding

MINING_PORTS = frozenset({3333, 4444, 5555, 14444})
TEMP_PREFIXES = ("/tmp/", "/var/tmp/", "/dev/shm/")
DEFAULT_SPIKE_BPS = 5.0 * 1024 * 1024
DEFAULT_SPIKE_RATIO = 4.0
DEFAULT_RETENTION_SECONDS = 900.0
DEFAULT_COOLDOWN_SECONDS = 120.0
MAX_RATE_SAMPLES = 12


def normalize_executable(exe: str) -> str:
    value = (exe or "").strip()
    if value.endswith(" (deleted)"):
        value = value[: -len(" (deleted)")]
    return value


def is_suspicious_executable(exe: str, cmdline: str = "") -> bool:
    """Return True for binaries running from volatile world-writable paths.

    AppImage runtimes are mounted below ``/tmp/.mount_*`` by design.  They are
    not flagged when the command line identifies the outer ``.AppImage`` file,
    which avoids a noisy false positive for every portable application.
    """
    value = normalize_executable(exe)
    if not value:
        return False
    try:
        real = os.path.realpath(value)
    except OSError:
        real = value
    command = cmdline or ""
    for candidate in (value, real):
        if not any(candidate == prefix.rstrip("/") or candidate.startswith(prefix) for prefix in TEMP_PREFIXES):
            continue
        if "/.mount_" in candidate and ".appimage" in command.lower():
            continue
        return True
    return False


def is_public_ip(value: str) -> bool:
    """Return True only for globally routable unicast addresses."""
    try:
        address = ipaddress.ip_address((value or "").strip())
    except (TypeError, ValueError):
        return False
    return bool(address.is_global)


def _unique_positive_ints(values) -> list[int]:
    result: list[int] = []
    for value in values or []:
        try:
            number = int(value)
        except (TypeError, ValueError):
            continue
        if number > 0 and number not in result:
            result.append(number)
    return result


class SecurityEngine:
    """Stateful local analyzer with de-duplication and short-term history."""

    def __init__(self) -> None:
        self._history: OrderedDict[str, SecurityFinding] = OrderedDict()
        self._rates: dict[str, deque[float]] = defaultdict(
            lambda: deque(maxlen=MAX_RATE_SAMPLES)
        )

    def clear(self) -> None:
        self._history.clear()
        self._rates.clear()

    def analyze(
        self,
        rows: list[dict],
        sockets: list,
        *,
        path_check: bool = True,
        mining_check: bool = True,
        upload_check: bool = True,
        spike_bps: float = DEFAULT_SPIKE_BPS,
        spike_ratio: float = DEFAULT_SPIKE_RATIO,
        retention_seconds: float = DEFAULT_RETENTION_SECONDS,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        now: float | None = None,
    ) -> dict:
        """Analyze one snapshot and return findings plus external endpoints.

        ``rows`` are the same dictionaries the live table uses, after cgroup
        grouping.  ``sockets`` are the engine's ``SocketRecord`` objects.  The
        returned dictionary is safe to pass directly to the GUI.
        """
        timestamp = time.time() if now is None else float(now)
        sockets_by_pid: dict[int, list] = defaultdict(list)
        for socket_record in sockets or []:
            for pid in _unique_positive_ints(getattr(socket_record, "pids", ())):
                sockets_by_pid[pid].append(socket_record)

        for row in rows or []:
            pids = _unique_positive_ints(
                row.get("pids") or [row.get("pid")]
            )
            if not pids:
                continue
            key_base = (
                str(row.get("app_key") or "")
                or normalize_executable(str(row.get("exe") or ""))
                or f"pid:{pids[0]}"
            )
            name = str(row.get("name") or "")
            exe = normalize_executable(str(row.get("exe") or ""))
            cmdline = str(row.get("cmdline") or "")
            primary_pid = pids[0]

            if path_check and is_suspicious_executable(exe, cmdline):
                self._record(
                    key=f"temp-path:{key_base}",
                    kind="temp_path",
                    severity="high",
                    timestamp=timestamp,
                    cooldown_seconds=cooldown_seconds,
                    pid=primary_pid,
                    pids=pids,
                    app_key=key_base,
                    name=name,
                    exe=exe,
                    detail=exe,
                )

            if mining_check:
                seen_endpoints: set[tuple[str, int]] = set()
                for pid in pids:
                    for socket_record in sockets_by_pid.get(pid, ()):
                        port = int(getattr(socket_record, "remote_port", 0) or 0)
                        if port not in MINING_PORTS:
                            continue
                        remote_ip = str(getattr(socket_record, "remote_addr", "") or "")
                        if not remote_ip or not is_public_ip(remote_ip):
                            continue
                        endpoint = (remote_ip, port)
                        if endpoint in seen_endpoints:
                            continue
                        seen_endpoints.add(endpoint)
                        self._record(
                            key=f"mining-port:{key_base}:{remote_ip}:{port}",
                            kind="mining_port",
                            severity="critical",
                            timestamp=timestamp,
                            cooldown_seconds=cooldown_seconds,
                            pid=primary_pid,
                            pids=pids,
                            app_key=key_base,
                            name=name,
                            exe=exe,
                            remote_ip=remote_ip,
                            remote_port=port,
                            detail=f"{remote_ip}:{port}" if remote_ip else str(port),
                        )

            if upload_check:
                rate_key = key_base
                rate = max(0.0, float(row.get("up_bps", 0.0) or 0.0))
                samples = self._rates[rate_key]
                if len(samples) >= 1 and rate >= max(0.0, float(spike_bps)):
                    baseline = sum(samples) / len(samples)
                    if baseline <= 0 or rate >= baseline * max(1.0, float(spike_ratio)):
                        self._record(
                            key=f"upload-spike:{rate_key}",
                            kind="upload_spike",
                            severity="high",
                            timestamp=timestamp,
                            cooldown_seconds=cooldown_seconds,
                            pid=primary_pid,
                            pids=pids,
                            app_key=key_base,
                            name=name,
                            exe=exe,
                            detail=f"{rate:.0f}",
                            extra={
                                "up_bps": rate,
                                "baseline_bps": baseline,
                                "ratio": rate / baseline if baseline else 0.0,
                            },
                        )
                samples.append(rate)

        self._prune(timestamp, retention_seconds)
        findings = sorted(
            self._history.values(),
            key=lambda item: (
                -SEVERITY_ORDER.get(item.severity, 0),
                -item.last_seen,
            ),
        )
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for finding in findings:
            if finding.severity in counts:
                counts[finding.severity] += 1

        return {
            "findings": [finding.to_dict() for finding in findings],
            "counts": {**counts, "total": len(findings)},
            "external_ips": self._external_ips(rows or [], sockets or []),
            "generated": timestamp,
        }

    def _record(
        self,
        *,
        key: str,
        kind: str,
        severity: str,
        timestamp: float,
        cooldown_seconds: float,
        pid: int,
        pids: list[int],
        app_key: str,
        name: str,
        exe: str,
        remote_ip: str = "",
        remote_port: int = 0,
        detail: str = "",
        extra: dict | None = None,
    ) -> None:
        current = self._history.get(key)
        if current is not None:
            current.last_seen = timestamp
            current.pid = pid or current.pid
            current.pids = pids or current.pids
            current.name = name or current.name
            current.exe = exe or current.exe
            current.remote_ip = remote_ip or current.remote_ip
            current.remote_port = remote_port or current.remote_port
            current.detail = detail or current.detail
            if extra:
                current.extra.update(extra)
            if timestamp - current.last_alert >= max(0.0, cooldown_seconds):
                current.count += 1
                current.last_alert = timestamp
            return
        finding = SecurityFinding(
            key=key,
            kind=kind,
            severity=severity,
            pid=pid,
            pids=list(pids),
            app_key=app_key,
            name=name,
            exe=exe,
            remote_ip=remote_ip,
            remote_port=remote_port,
            first_seen=timestamp,
            last_seen=timestamp,
            last_alert=timestamp,
            count=1,
            detail=detail,
            extra=dict(extra or {}),
        )
        self._history[key] = finding

    def _prune(self, now: float, retention_seconds: float) -> None:
        cutoff = now - max(0.0, retention_seconds)
        for key, finding in list(self._history.items()):
            if finding.last_seen < cutoff:
                del self._history[key]

    @staticmethod
    def external_ips(rows: list[dict], sockets: list) -> list[dict]:
        return SecurityEngine._external_ips(rows, sockets)

    @staticmethod
    def _external_ips(rows: list[dict], sockets: list) -> list[dict]:
        names_by_pid: dict[int, str] = {}
        for row in rows:
            for pid in _unique_positive_ints(row.get("pids") or [row.get("pid")]):
                if row.get("name"):
                    names_by_pid[pid] = str(row["name"])
        endpoints: dict[str, dict] = {}
        for socket_record in sockets:
            remote_ip = str(getattr(socket_record, "remote_addr", "") or "")
            if not is_public_ip(remote_ip):
                continue
            entry = endpoints.setdefault(
                remote_ip,
                {"ip": remote_ip, "ports": set(), "pids": set(), "names": set()},
            )
            port = int(getattr(socket_record, "remote_port", 0) or 0)
            if port:
                entry["ports"].add(port)
            for pid in _unique_positive_ints(getattr(socket_record, "pids", ())):
                entry["pids"].add(pid)
                if pid in names_by_pid:
                    entry["names"].add(names_by_pid[pid])
        result = []
        for entry in endpoints.values():
            result.append(
                {
                    "ip": entry["ip"],
                    "ports": sorted(entry["ports"]),
                    "pids": sorted(entry["pids"]),
                    "names": sorted(entry["names"]),
                }
            )
        result.sort(key=lambda item: ipaddress.ip_address(item["ip"]))
        return result
