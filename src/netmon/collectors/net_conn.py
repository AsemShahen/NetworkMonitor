from __future__ import annotations

"""Helpers for mapping kernel socket inodes to processes and cgroups.

The network engines return a socket ``inode``.  Linux exposes the owning
process through ``/proc/<pid>/fd`` and the cgroup through
``/proc/<pid>/cgroup``.  Keeping those helpers here means the Netlink, ss and
``/proc/net`` engines all group applications the same way.
"""

import os
import re
import socket
import struct
from collections import defaultdict
from dataclasses import dataclass, field

_SYSTEMD_ESCAPE_RE = re.compile(r"\\x([0-9a-fA-F]{2})")
_FLATPAK_RE = re.compile(r"^app-flatpak-(.+?)-(\d+)\.scope$")
_FLATPAK_SIMPLE_RE = re.compile(r"^app-flatpak-(.+)\.scope$")
_SNAP_RE = re.compile(r"^snap\.([^.]+)\.(.+)\.scope$")

FLATPAK_NAMES = {
    "ai.lmstudio.lm-studio": "LM Studio",
    "com.discordapp.Discord": "Discord",
    "com.spotify.Client": "Spotify",
    "com.visualstudio.code": "Visual Studio Code",
    "org.mozilla.firefox": "Firefox",
    "org.telegram.desktop": "Telegram",
    "org.chromium.Chromium": "Chromium",
    "org.gnome.Builder": "GNOME Builder",
    "io.github.ungoogled_software.ungoogled_chromium": "ungoogled-chromium",
}


@dataclass
class ProcSocket:
    """A socket discovered from /proc/net (no byte counters)."""

    inode: int
    protocol: str
    state: str = ""
    uid: int = -1
    tx_queue: int = 0
    rx_queue: int = 0
    family: int = 4
    local_addr: str = ""
    local_port: int = 0
    remote_addr: str = ""
    remote_port: int = 0


@dataclass
class SocketRecord:
    """A socket returned by a byte-counting engine (Netlink or ss)."""

    inode: int
    protocol: str
    state: int | str = 0
    uid: int = -1
    tx: int = 0
    rx: int = 0
    measured: bool = False
    pids: list[int] = field(default_factory=list)
    name: str = ""
    cgroup: str = ""
    local_addr: str = ""
    local_port: int = 0
    remote_addr: str = ""
    remote_port: int = 0


def split_endpoint(value: str) -> tuple[str, int]:
    """Split ``address:port`` from ss/proc output, including IPv6 brackets."""
    text = (value or "").strip()
    if not text or text in ("*", "*:*", "0.0.0.0:*", "[::]:*"):
        return "", 0
    if text.startswith("["):
        host, _, port = text[1:].partition("]:")
    else:
        host, sep, port = text.rpartition(":")
        if not sep:
            return text.strip("[]"), 0
    host = host.strip().strip("[]")
    if host in ("*", "0.0.0.0", "::"):
        host = ""
    try:
        port_number = int(port)
    except (TypeError, ValueError):
        port_number = 0
    return host, max(0, min(65535, port_number))


def format_netlink_address(value, family: int) -> str:
    """Convert a pyroute2 inet_diag address (bytes/list/str) to text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
    else:
        try:
            raw = bytes(int(part) & 0xFF for part in value)
        except (TypeError, ValueError):
            return ""
    expected = 4 if family == socket.AF_INET else 16
    if len(raw) < expected:
        return ""
    try:
        return socket.inet_ntop(family, raw[:expected])
    except (OSError, ValueError):
        return ""


def format_netlink_port(value) -> int:
    if value is None:
        return 0
    try:
        if isinstance(value, (bytes, bytearray, memoryview)):
            return int.from_bytes(bytes(value), "big") & 0xFFFF
        return int(value) & 0xFFFF
    except (TypeError, ValueError, OverflowError):
        return 0


def _parse_proc_endpoint(value: str, family: int) -> tuple[str, int]:
    """Decode the little-endian address:port representation in /proc/net."""
    try:
        address_hex, port_hex = value.split(":", 1)
        port_number = int(port_hex, 16)
        if family == socket.AF_INET:
            raw = struct.pack("<I", int(address_hex, 16))
        else:
            words = [address_hex[i : i + 8] for i in range(0, len(address_hex), 8)]
            raw = b"".join(struct.pack("<I", int(word, 16)) for word in words)
        return socket.inet_ntop(family, raw), port_number
    except (ValueError, OSError, struct.error):
        return "", 0


def _unescape_systemd(value: str) -> str:
    """Decode the \\xNN escapes used in systemd unit/cgroup names."""

    def repl(match: re.Match[str]) -> str:
        try:
            return chr(int(match.group(1), 16))
        except ValueError:
            return match.group(0)

    return _SYSTEMD_ESCAPE_RE.sub(repl, value)


def _display_name(app_id: str) -> str:
    if app_id in FLATPAK_NAMES:
        return FLATPAK_NAMES[app_id]
    tail = app_id.rsplit(".", 1)[-1]
    return tail.replace("-", " ").replace("_", " ").strip().title() or app_id


def cgroup_app_key(path: str) -> tuple[str, str]:
    """Return a stable ``(app_key, display_name)`` for a cgroup path.

    Flatpak scopes contain a per-launch numeric suffix; Snap scopes contain an
    instance name.  Both are normalised so the same application is counted as
    one row across restarts.
    """
    if not path:
        return "", ""
    for segment in reversed(path.split("/")):
        segment = _unescape_systemd(segment.strip())
        if not segment:
            continue
        match = _FLATPAK_RE.match(segment)
        if match is None:
            match = _FLATPAK_SIMPLE_RE.match(segment)
        if match is not None:
            app_id = match.group(1)
            return f"flatpak:{app_id}", _display_name(app_id)
        match = _SNAP_RE.match(segment)
        if match is not None:
            name = match.group(1)
            return f"snap:{name}", _display_name(name)
    return "", ""


def pid_cgroup(pid: int) -> str:
    """Read the unified cgroup path for a PID (cgroup v2), or the last v1 path."""
    try:
        with open(f"/proc/{pid}/cgroup", "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except (OSError, PermissionError):
        return ""
    last = ""
    for line in lines:
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        hierarchy, controllers, path = parts
        path = path.strip()
        if hierarchy == "0" and not controllers:
            return path
        if path and path != "/":
            last = path
    return last


def app_key_for(exe: str, cgroup: str = "", cmdline: str = "") -> tuple[str, str]:
    """Return ``(app_key, display_name)`` for usage/grouping.

    Flatpak and Snap use their stable cgroup identity.  AppImages are keyed by
    the outer ``.AppImage`` file because their mount path changes on every run.
    Other programs use their executable path.
    """
    ckey, cname = cgroup_app_key(cgroup)
    if ckey:
        return ckey, cname

    first_arg = (cmdline or "").split(" ", 1)[0]
    if first_arg.endswith(".AppImage") or "/.mount_" in (exe or ""):
        base = os.path.basename(first_arg) if first_arg.endswith(".AppImage") else os.path.basename(exe)
        if base:
            return f"appimage:{base}", os.path.splitext(base)[0]
    if exe:
        return f"exe:{exe}", ""
    return "", ""


def inode_to_pids(inodes: set[int] | None = None) -> dict[int, list[int]]:
    """Map socket inodes to PIDs by walking /proc/<pid>/fd.

    ``inodes`` limits the walk to the sockets we actually need, which keeps the
    cost low when Netlink returns hundreds of sockets.  Sockets belonging to
    other users are simply not visible and remain unattributed.
    """
    result: dict[int, list[int]] = defaultdict(list)
    try:
        entries = list(os.scandir("/proc"))
    except OSError:
        return {}
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        fd_dir = f"/proc/{pid}/fd"
        try:
            fds = os.listdir(fd_dir)
        except (OSError, PermissionError):
            continue
        for fd in fds:
            try:
                link = os.readlink(f"{fd_dir}/{fd}")
            except (OSError, PermissionError):
                continue
            if not link.startswith("socket:["):
                continue
            try:
                inode = int(link[8:-1])
            except ValueError:
                continue
            if inodes is not None and inode not in inodes:
                continue
            result[inode].append(pid)
    return {inode: sorted(set(pids)) for inode, pids in result.items()}


def _parse_proc_net(path: str, protocol: str, family: int) -> list[ProcSocket]:
    sockets: list[ProcSocket] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[1:]
    except (OSError, PermissionError):
        return sockets
    for line in lines:
        parts = line.split()
        if len(parts) < 10:
            continue
        try:
            state = parts[3]
            if protocol == "tcp" and state == "0A":  # LISTEN
                continue
            uid = int(parts[7])
            inode = int(parts[9])
            tx_rx = parts[4].split(":", 1)
            tx_queue = int(tx_rx[0], 16) if len(tx_rx) == 2 else 0
            rx_queue = int(tx_rx[1], 16) if len(tx_rx) == 2 else 0
            local_addr, local_port = _parse_proc_endpoint(parts[1], family)
            remote_addr, remote_port = _parse_proc_endpoint(parts[2], family)
        except (ValueError, IndexError):
            continue
        if inode <= 0:
            continue
        sockets.append(
            ProcSocket(
                inode=inode,
                protocol=protocol,
                state=state,
                uid=uid,
                tx_queue=tx_queue,
                rx_queue=rx_queue,
                family=family,
                local_addr=local_addr,
                local_port=local_port,
                remote_addr=remote_addr,
                remote_port=remote_port,
            )
        )
    return sockets


def read_proc_net_sockets() -> list[ProcSocket]:
    """Read TCP/UDP socket metadata from /proc/net (no cumulative counters)."""
    sockets: list[ProcSocket] = []
    for path, protocol, family in (
        ("/proc/net/tcp", "tcp", 4),
        ("/proc/net/tcp6", "tcp", 6),
        ("/proc/net/udp", "udp", 4),
        ("/proc/net/udp6", "udp", 6),
    ):
        sockets.extend(_parse_proc_net(path, protocol, family))
    return sockets


def get_active_pids() -> set[int]:
    """Compatibility helper: PIDs with at least one non-listening socket."""
    sockets = read_proc_net_sockets()
    if not sockets:
        return set()
    mapping = inode_to_pids({s.inode for s in sockets})
    pids: set[int] = set()
    for socket in sockets:
        pids.update(mapping.get(socket.inode, ()))
    return pids
