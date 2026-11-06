from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field

from .net_conn import (
    SocketRecord,
    inode_to_pids,
    pid_cgroup,
    read_proc_net_sockets,
)
from .netlink import NetlinkBackend

from ..i18n import tr

STATE_TOKENS = {
    "ESTAB", "LISTEN", "SYN-SENT", "SYN-RECV", "FIN-WAIT-1", "FIN-WAIT-2",
    "TIME-WAIT", "CLOSE-WAIT", "LAST-ACK", "CLOSING", "CLOSE", "UNCONN",
    "UNKNOWN", "BOUND",
}
USERS_RE = re.compile(r'\("([^"]+)",pid=(\d+),fd=(\d+)\)')
INODE_RE = re.compile(r"\bino:(\d+)")
CGROUP_RE = re.compile(r"cgroup:(\S+)")
BYTES_SENT_RE = re.compile(r"bytes_sent:(\d+)")
BYTES_RECV_RE = re.compile(r"bytes_received:(\d+)")
BYTES_ACKED_RE = re.compile(r"bytes_acked:(\d+)")


@dataclass
class NetCounters:
    pid: int
    name: str = ""
    tx: int = 0
    rx: int = 0
    tcp_sockets: int = 0
    udp_sockets: int = 0
    sockets: int = 0
    measured_sockets: int = 0
    unmeasured_udp: int = 0

    @property
    def has_unmeasured(self) -> bool:
        return self.unmeasured_udp > 0


@dataclass
class SampleResult:
    counters: dict[int, NetCounters] = field(default_factory=dict)
    down_bps: dict[int, float] = field(default_factory=dict)
    up_bps: dict[int, float] = field(default_factory=dict)
    down_bytes: dict[int, int] = field(default_factory=dict)
    up_bytes: dict[int, int] = field(default_factory=dict)
    active_pids: set[int] = field(default_factory=set)
    sockets: list[SocketRecord] = field(default_factory=list)
    dt: float = 0.0
    source: str = ""
    error: str | None = None
    diagnostics: dict = field(default_factory=dict)


@dataclass
class _PrevSocket:
    tx: int
    rx: int
    protocol: str
    pid: int | None


def parse_ss_sockets(text: str, udp: bool = False) -> list[SocketRecord]:
    """Parse ``ss -tinape`` / ``ss -uanpe`` into per-socket records.

    The parser keeps the inode so the engine can calculate deltas per socket
    instead of per PID.  A PID can own several sockets, and a socket can close
    while another one opens; per-inode tracking avoids losing or double
    counting bytes in both cases.
    """
    sockets: list[SocketRecord] = []
    current: dict | None = None

    def flush() -> None:
        nonlocal current
        if current is None:
            return
        if current["state"] == "LISTEN":
            current = None
            return
        inode = current["inode"]
        if not inode:
            current = None
            return
        pids = current["pids"]
        measured = bool(current["saw_bytes"]) and not udp
        sockets.append(
            SocketRecord(
                inode=inode,
                protocol="udp" if udp else "tcp",
                state=current["state"],
                uid=-1,
                tx=current["tx"],
                rx=current["rx"],
                measured=measured,
                pids=list(pids),
                name=current["name"],
                cgroup=current["cgroup"],
            )
        )
        current = None

    for raw in text.splitlines():
        line = raw.strip("\n")
        if not line.strip():
            continue
        stripped = line.strip()
        tokens = stripped.split()
        if stripped.startswith(("State", "Netid", "Recv-Q")):
            continue
        is_header = bool(tokens) and tokens[0] in STATE_TOKENS
        if is_header:
            flush()
            users = USERS_RE.findall(line)
            inode_match = INODE_RE.search(line)
            cgroup_match = CGROUP_RE.search(line)
            current = {
                "state": tokens[0],
                "inode": int(inode_match.group(1)) if inode_match else 0,
                "pids": [int(pid) for _, pid, _ in users],
                "name": users[0][0] if users else "",
                "cgroup": cgroup_match.group(1) if cgroup_match else "",
                "tx": 0,
                "rx": 0,
                "saw_bytes": False,
            }
            # Some ss versions put byte counters on the header line itself.
            self_tx = BYTES_SENT_RE.search(line)
            self_rx = BYTES_RECV_RE.search(line)
            if self_tx:
                current["tx"] += int(self_tx.group(1))
                current["saw_bytes"] = True
            if self_rx:
                current["rx"] += int(self_rx.group(1))
                current["saw_bytes"] = True
            continue
        if current is None:
            continue
        tx_match = BYTES_SENT_RE.search(line)
        rx_match = BYTES_RECV_RE.search(line)
        acked_match = BYTES_ACKED_RE.search(line)
        if tx_match:
            current["tx"] += int(tx_match.group(1))
            current["saw_bytes"] = True
        elif acked_match and not current["saw_bytes"]:
            current["tx"] += int(acked_match.group(1))
            current["saw_bytes"] = True
        if rx_match:
            current["rx"] += int(rx_match.group(1))
            current["saw_bytes"] = True
    flush()
    return sockets


def parse_ss(text: str, udp: bool = False) -> dict[int, NetCounters]:
    """Backward-compatible per-PID aggregation used by older tests/callers."""
    result: dict[int, NetCounters] = {}
    for socket in parse_ss_sockets(text, udp=udp):
        if not socket.pids:
            continue
        pid = socket.pids[0]
        counters = result.get(pid)
        if counters is None:
            counters = NetCounters(pid=pid, name=socket.name)
            result[pid] = counters
        if not counters.name and socket.name:
            counters.name = socket.name
        counters.tx += socket.tx
        counters.rx += socket.rx
        counters.sockets += 1
        if udp:
            counters.udp_sockets += 1
            if not socket.measured:
                counters.unmeasured_udp += 1
        else:
            counters.tcp_sockets += 1
            if socket.measured:
                counters.measured_sockets += 1
    return result


def find_ss() -> str | None:
    """Find ss without trusting PATH alone (GUI launchers can have a minimal PATH)."""
    candidates = [
        shutil.which("ss"),
        "/bin/ss",
        "/usr/bin/ss",
        "/usr/sbin/ss",
        "/sbin/ss",
    ]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def _run_ss(ss_path: str, args: list[str]) -> tuple[str, str | None]:
    try:
        proc = subprocess.run(
            [ss_path] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=6,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return "", str(exc)
    if proc.returncode != 0 and not (proc.stdout or "").strip():
        error = (proc.stderr or "").strip() or f"ss exited with code {proc.returncode}"
        return "", error
    return proc.stdout or "", None


class _SSBackend:
    def __init__(self) -> None:
        self.path: str | None = None
        self.last_error: str | None = None

    def poll(self) -> tuple[list[SocketRecord], str | None]:
        self.path = find_ss()
        if not self.path:
            self.last_error = "ss was not found"
            return [], self.last_error
        tcp_text, tcp_error = _run_ss(self.path, ["-tinape"])
        udp_text, udp_error = _run_ss(self.path, ["-uanpe"])
        records = parse_ss_sockets(tcp_text, udp=False)
        records.extend(parse_ss_sockets(udp_text, udp=True))
        if not records and (tcp_error or udp_error):
            self.last_error = tcp_error or udp_error
            return [], self.last_error
        self.last_error = tcp_error or udp_error
        return records, None


class _ProcBackend:
    def poll(self) -> list[SocketRecord]:
        proc_sockets = read_proc_net_sockets()
        if not proc_sockets:
            return []
        mapping = inode_to_pids({socket.inode for socket in proc_sockets})
        records: list[SocketRecord] = []
        for socket in proc_sockets:
            pids = mapping.get(socket.inode, [])
            cgroup = pid_cgroup(pids[0]) if pids else ""
            records.append(
                SocketRecord(
                    inode=socket.inode,
                    protocol=socket.protocol,
                    state=socket.state,
                    uid=socket.uid,
                    tx=0,
                    rx=0,
                    measured=False,
                    pids=pids,
                    cgroup=cgroup,
                )
            )
        return records


class TrafficEngine:
    """Per-socket traffic engine.

    Order of preference:

    1. Netlink (pyroute2 ``DiagSocket``) — real TCP counters.
    2. ``ss`` — fallback with the same per-inode counters.
    3. ``/proc/net`` — connection discovery only; no byte counters.
    """

    def __init__(self) -> None:
        self._netlink = NetlinkBackend()
        self._ss = _SSBackend()
        self._proc = _ProcBackend()
        self._prev: dict[int, _PrevSocket] = {}
        self._last_ts: float = 0.0
        self._last_source = ""
        self.last_error: str | None = None
        self.last_diagnostics: dict = {}

    def reset_baseline(self) -> None:
        """Forget per-socket counters so the next sample starts a new baseline.

        This is used when the GUI takes over usage writing from the background
        collector.  Without it, the first GUI sample would include traffic that
        the collector already recorded.
        """
        self._prev.clear()
        self._last_ts = 0.0
        self._last_source = ""

    @property
    def available(self) -> bool:
        if self._last_source:
            return self._last_source in ("netlink", "ss")
        return self._netlink.available or find_ss() is not None

    def describe(self) -> str:
        if self._last_source == "netlink":
            return tr("source.netlink")
        if self._last_source == "ss":
            return tr("source.ss")
        if self._last_source == "proc-net":
            return tr("source.proc")
        return tr("source.detecting")

    def _collect(self) -> tuple[list[SocketRecord], str, str | None, str | None, str | None]:
        records, netlink_error = self._netlink.poll()
        if records or netlink_error is None:
            return records, "netlink", None, netlink_error, None

        records, ss_error = self._ss.poll()
        if records or ss_error is None:
            return records, "ss", None, netlink_error, ss_error

        records = self._proc.poll()
        return records, "proc-net", tr("error.no_counters"), netlink_error, ss_error

    def poll(self) -> SampleResult:
        now = time.monotonic()
        had_baseline = self._last_ts != 0.0
        dt = now - self._last_ts if had_baseline else 0.0
        self._last_ts = now
        result = SampleResult(dt=dt)

        records, source, error, netlink_error, ss_error = self._collect()
        source_changed = source != self._last_source
        if source_changed:
            self._prev.clear()
        self._last_source = source

        mapping = inode_to_pids({record.inode for record in records})
        for record in records:
            if not record.pids:
                record.pids = mapping.get(record.inode, [])
            if not record.cgroup and record.pids:
                record.cgroup = pid_cgroup(record.pids[0])

        counters: dict[int, NetCounters] = {}
        down_bytes: dict[int, int] = {}
        up_bytes: dict[int, int] = {}
        active_pids: set[int] = set()
        attributed = 0
        tcp_count = 0
        udp_count = 0
        udp_unmeasured = 0
        seen_inodes: set[int] = set()

        for record in records:
            if record.protocol == "tcp":
                tcp_count += 1
            else:
                udp_count += 1
                if not record.measured:
                    udp_unmeasured += 1
            primary = record.pids[0] if record.pids else None
            if primary is not None:
                attributed += 1
                active_pids.add(primary)
                nc = counters.get(primary)
                if nc is None:
                    nc = NetCounters(pid=primary, name=record.name)
                    counters[primary] = nc
                if not nc.name and record.name:
                    nc.name = record.name
                nc.tx += record.tx
                nc.rx += record.rx
                nc.sockets += 1
                if record.protocol == "tcp":
                    nc.tcp_sockets += 1
                    if record.measured:
                        nc.measured_sockets += 1
                else:
                    nc.udp_sockets += 1
                    if not record.measured:
                        nc.unmeasured_udp += 1

            if not record.measured:
                continue
            seen_inodes.add(record.inode)
            previous = self._prev.get(record.inode)
            d_rx = d_tx = 0
            if previous is not None and previous.protocol == record.protocol:
                if record.rx >= previous.rx:
                    d_rx = record.rx - previous.rx
                if record.tx >= previous.tx:
                    d_tx = record.tx - previous.tx
            elif had_baseline and not source_changed:
                # The socket was created after the previous sample, so its
                # cumulative counters are entirely new traffic.
                d_rx = max(0, record.rx)
                d_tx = max(0, record.tx)
            self._prev[record.inode] = _PrevSocket(
                tx=record.tx,
                rx=record.rx,
                protocol=record.protocol,
                pid=primary,
            )
            if primary is not None:
                down_bytes[primary] = down_bytes.get(primary, 0) + d_rx
                up_bytes[primary] = up_bytes.get(primary, 0) + d_tx

        # Drop counters for sockets that have gone away.
        for inode in list(self._prev):
            if inode not in seen_inodes:
                del self._prev[inode]

        if dt > 0:
            result.down_bps = {pid: value / dt for pid, value in down_bytes.items()}
            result.up_bps = {pid: value / dt for pid, value in up_bytes.items()}
        result.down_bytes = down_bytes
        result.up_bytes = up_bytes
        result.counters = counters
        result.active_pids = active_pids
        result.sockets = records
        result.source = source
        result.error = error
        result.diagnostics = {
            "engine": source,
            "engine_ok": source in ("netlink", "ss"),
            "netlink_ok": netlink_error is None,
            "netlink_error": netlink_error,
            "ss_path": self._ss.path or find_ss(),
            "ss_ok": ss_error is None and (self._ss.path is not None or find_ss() is not None),
            "ss_error": ss_error,
            "sockets": len(records),
            "attributed": attributed,
            "unattributed": max(0, len(records) - attributed),
            "tcp": tcp_count,
            "udp": udp_count,
            "udp_unmeasured": udp_unmeasured,
        }
        self.last_error = error
        self.last_diagnostics = result.diagnostics
        return result
