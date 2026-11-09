from __future__ import annotations

from dataclasses import dataclass, field, asdict


SEVERITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass
class SecurityFinding:
    """A single local heuristic finding shown in the Security tab."""

    key: str
    kind: str
    severity: str
    pid: int = 0
    pids: list[int] = field(default_factory=list)
    app_key: str = ""
    name: str = ""
    exe: str = ""
    remote_ip: str = ""
    remote_port: int = 0
    first_seen: float = 0.0
    last_seen: float = 0.0
    last_alert: float = 0.0
    count: int = 1
    detail: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["severity_rank"] = SEVERITY_ORDER.get(self.severity, 0)
        return data


@dataclass
class IPReputation:
    """Normalized IP reputation returned by AbuseIPDB or VirusTotal."""

    ip: str
    provider: str
    ok: bool = True
    score: int = 0
    reports: int = 0
    malicious: bool = False
    country: str = ""
    isp: str = ""
    usage: str = ""
    checked: float = 0.0
    cached: bool = False
    error_key: str = ""
    error_args: dict = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileReputation:
    """Normalized file hash result returned by MalwareBazaar or VirusTotal."""

    path: str
    sha256: str
    provider: str
    ok: bool = True
    malicious: bool = False
    detections: int = 0
    total: int = 0
    file_name: str = ""
    signatures: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    checked: float = 0.0
    cached: bool = False
    error_key: str = ""
    error_args: dict = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
