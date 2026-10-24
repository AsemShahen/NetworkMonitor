from __future__ import annotations

import re
import shutil
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field

from .net_conn import get_active_pids

STATE_TOKENS = {
    "ESTAB", "LISTEN", "SYN-SENT", "SYN-RECV", "FIN-WAIT-1", "FIN-WAIT-2",
    "TIME-WAIT", "CLOSE-WAIT", "LAST-ACK", "CLOSING", "CLOSE", "UNCONN",
    "UNKNOWN", "BOUND",
}
USERS_RE = re.compile(r'users:\(\("([^"]+)",pid=(\d+),fd=(\d+)\)')
INODE_RE = re.compile(r"\bino:(\d+)")
BYTES_SENT_RE = re.compile(r"bytes_sent:(\d+)")
BYTES_RECV_RE = re.compile(r"bytes_received:(\d+)")


@dataclass
class NetCounters:
    pid: int
    name: str = ""
    tx: int = 0
    rx: int = 0
    tcp_sockets: int = 0
    udp_sockets: int = 0
    sockets: int = 0


@dataclass
class SampleResult:
    counters: dict[int, NetCounters] = field(default_factory=dict)
    down_bps: dict[int, float] = field(default_factory=dict)
    up_bps: dict[int, float] = field(default_factory=dict)
    down_bytes: dict[int, int] = field(default_factory=dict)
    up_bytes: dict[int, int] = field(default_factory=dict)
    active_pids: set[int] = field(default_factory=set)
    dt: float = 0.0
    source: str = ""
    error: str | None = None


def parse_ss(text: str, udp: bool = False) -> dict[int, NetCounters]:
    """تحليل مخرجات `ss -tinape` / `ss -uanpe` إلى عدّادات لكل PID.

    يعتمد على أن كل مقبس يبدأ بسطر حالته، وأن بيانات tcp_info
    (bytes_sent / bytes_received) تأتي في الأسطر التالية.
    """
    result: dict[int, NetCounters] = {}
    cur_pid: int | None = None
    cur_name = ""
    cur_inode: int | None = None
    cur_state = ""
    cur_tx = 0
    cur_rx = 0
    cur_counted = False

    def flush() -> None:
        nonlocal cur_pid, cur_name, cur_inode, cur_state, cur_tx, cur_rx, cur_counted
        if cur_pid is not None and not (cur_state == "LISTEN" and not (cur_tx or cur_rx)):
            nc = result.get(cur_pid)
            if nc is None:
                nc = NetCounters(pid=cur_pid, name=cur_name)
                result[cur_pid] = nc
            if not nc.name and cur_name:
                nc.name = cur_name
            nc.tx += cur_tx
            nc.rx += cur_rx
            nc.sockets += 1
            if udp:
                nc.udp_sockets += 1
            else:
                nc.tcp_sockets += 1
        cur_pid = None
        cur_name = ""
        cur_inode = None
        cur_state = ""
        cur_tx = 0
        cur_rx = 0
        cur_counted = False

    for raw in text.splitlines():
        line = raw.strip("\n")
        if not line.strip():
            continue
        stripped = line.strip()
        tokens = stripped.split()
        is_header = bool(tokens) and tokens[0] in STATE_TOKENS
        if stripped.startswith(("State", "Netid", "Recv-Q")):
            continue
        if is_header:
            flush()
            cur_state = tokens[0]
            m = USERS_RE.search(line)
            if m:
                cur_name = m.group(1)
                cur_pid = int(m.group(2))
            m2 = INODE_RE.search(line)
            if m2:
                cur_inode = int(m2.group(1))
            continue
        # سطر تفاصيل يخص المقبس الحالي
        if cur_pid is None:
            continue
        m_tx = BYTES_SENT_RE.search(line)
        m_rx = BYTES_RECV_RE.search(line)
        if m_tx or m_rx:
            if m_tx:
                cur_tx += int(m_tx.group(1))
            if m_rx:
                cur_rx += int(m_rx.group(1))
            cur_counted = True
    flush()
    return result


def _run_ss(args: list[str]) -> str:
    ss = shutil.which("ss")
    if not ss:
        return ""
    try:
        proc = subprocess.run(
            [ss] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=6,
        )
        return proc.stdout or ""
    except (OSError, subprocess.SubprocessError):
        return ""


class TrafficEngine:
    """محرك حركة شبكة حقيقي يعتمد على عدّادات sock_diag عبر أداة ss.

    - يجمع البايتات التراكمية لكل مقبس (inode) ويحسب الفرق الزمني.
    - إن لم تتوفر أداة ss، يعود لكشف العمليات النشطة من /proc/net فقط.
    """

    def __init__(self) -> None:
        self._prev_pid: dict[int, tuple[int, int]] = {}
        self._last_ts: float = 0.0
        self._ss_available = shutil.which("ss") is not None
        self.last_error: str | None = None

    @property
    def available(self) -> bool:
        return self._ss_available

    def describe(self) -> str:
        if self._ss_available:
            return "sock_diag (ss)"
        return "كشف الاتصالات من /proc/net (بدون عدّادات)"

    def poll(self) -> SampleResult:
        now = time.monotonic()
        dt = now - self._last_ts if self._last_ts else 0.0
        self._last_ts = now
        result = SampleResult(dt=dt)

        if not self._ss_available:
            active = get_active_pids()
            result.active_pids = set(active)
            result.source = "proc-net"
            result.error = "أداة ss غير متوفرة (حزمة iproute2). لن تُعرض السرعات."
            self.last_error = result.error
            return result

        tcp_text = _run_ss(["-tinape"])
        udp_text = _run_ss(["-uanpe"])
        tcp = parse_ss(tcp_text, udp=False)
        udp = parse_ss(udp_text, udp=True)

        counters: dict[int, NetCounters] = {}
        for pid, nc in tcp.items():
            counters[pid] = nc
        for pid, nc in udp.items():
            if pid in counters:
                counters[pid].udp_sockets += nc.udp_sockets
            else:
                counters[pid] = nc

        # جعل مفاتيح التتبّع لكل مقبس أدق: نعيد بناءها من نص ss عبر inode.
        # بما أن parse_ss يجمّع لكل PID، نحسب الفرق على مستوى PID
        # مع معالجة انخفاض العداد (إغلاق مقبس) بعدم إنتاج قيم سالبة.
        for pid, nc in counters.items():
            prev = self._prev_pid.get(pid)
            ddown = dup = 0
            if prev is not None and dt > 0:
                drx = nc.rx - prev[0]
                dtx = nc.tx - prev[1]
                if drx >= 0:
                    ddown = drx
                if dtx >= 0:
                    dup = dtx
            self._prev_pid[pid] = (nc.rx, nc.tx)
            result.down_bytes[pid] = ddown
            result.up_bytes[pid] = dup
            if dt > 0:
                result.down_bps[pid] = ddown / dt
                result.up_bps[pid] = dup / dt

        # تنظيف PIDs التي اختفت
        alive = set(counters)
        for pid in list(self._prev_pid):
            if pid not in alive:
                del self._prev_pid[pid]

        result.counters = counters
        result.active_pids = set(counters)
        result.source = "ss"
        return result
