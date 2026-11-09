"""Lightweight local and reputation-based network security helpers.

The package is intentionally Qt-free so the same analyzer can be used by the
GUI, unit tests, and future headless tooling.
"""

from .heuristics import (
    MINING_PORTS,
    SecurityEngine,
    is_public_ip,
    is_suspicious_executable,
    normalize_executable,
)
from .models import FileReputation, IPReputation, SecurityFinding

__all__ = [
    "MINING_PORTS",
    "SecurityEngine",
    "SecurityFinding",
    "IPReputation",
    "FileReputation",
    "is_public_ip",
    "is_suspicious_executable",
    "normalize_executable",
]
