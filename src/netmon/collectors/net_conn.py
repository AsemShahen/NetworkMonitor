from __future__ import annotations

"""Helpers for mapping kernel socket inodes to processes and cgroups.

The network engines return a socket ``inode``.  Linux exposes the owning
process through ``/proc/<pid>/fd`` and the cgroup through
``/proc/<pid>/cgroup``.  Keeping those helpers here means the Netlink, ss and
``/proc/net`` engines all group applications the same way.
"""

import os
import re
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
