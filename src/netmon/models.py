from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProcInfo:
    """معلومات عملية واحدة تُجمع من /proc و محرك حركة الشبكة."""

    pid: int
    name: str = ""
    exe: str = ""
    cmdline: str = ""
    uid: int = -1
    state: str = "?"
    cpu: float = 0.0
    rss: int = 0
    down_bps: float = 0.0
    up_bps: float = 0.0
    down_total: int = 0
    up_total: int = 0
    udp_sockets: int = 0
    tcp_sockets: int = 0
    blocked: bool = False
    source: str = "proc"


@dataclass
class TrafficCounters:
    """عدّادات الشبكة التراكمية لعملية واحدة."""

    pid: int
    name: str = ""
    tx_bytes: int = 0
    rx_bytes: int = 0
    tcp_sockets: int = 0
    udp_sockets: int = 0
    ts: float = 0.0
    source: str = ""


@dataclass
class TrafficDelta:
    """مشتقات الفرق الزمني لبيانات شبكة عملية."""

    pid: int
    down_bps: float = 0.0
    up_bps: float = 0.0
    dt: float = 0.0


@dataclass
class SampleSet:
    """لقطة واحدة مجمعة لكل العمليات."""

    counters: dict[int, TrafficCounters] = field(default_factory=dict)
    ts: float = 0.0
    source: str = ""
    error: str | None = None


@dataclass
class BlockEntry:
    """إدخال محفوظ في قائمة الحظر."""

    exe: str
    slug: str
    name: str = ""
    when: float = 0.0

    def to_dict(self) -> dict:
        return {"exe": self.exe, "slug": self.slug, "name": self.name, "when": self.when}

    @classmethod
    def from_dict(cls, d: dict) -> "BlockEntry":
        return cls(exe=d.get("exe", ""), slug=d.get("slug", ""), name=d.get("name", ""), when=d.get("when", 0.0))