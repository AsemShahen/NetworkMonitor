from __future__ import annotations

import os
import re
import time

from .i18n import tr


def fmt_rate(bps: float, unit_auto: bool = True) -> str:
    """تحويل سرعة بالبايت/ثانية إلى نص مقروء (B/s, KB/s, MB/s, GB/s)."""
    try:
        v = max(0.0, float(bps))
    except (TypeError, ValueError):
        return "—"
    if v < 1024:
        return f"{v:0.0f} B/s"
    if v < 1024 ** 2:
        return f"{v / 1024:0.1f} KB/s"
    if v < 1024 ** 3:
        return f"{v / 1024 ** 2:0.2f} MB/s"
    return f"{v / 1024 ** 3:0.2f} GB/s"


def fmt_bytes(n: int | float) -> str:
    """تحويل حجم بالبايت إلى نص مقروء."""
    try:
        v = max(0.0, float(n))
    except (TypeError, ValueError):
        return "—"
    if v < 1024:
        return f"{v:0.0f} B"
    if v < 1024 ** 2:
        return f"{v / 1024:0.1f} KB"
    if v < 1024 ** 3:
        return f"{v / 1024 ** 2:0.1f} MB"
    return f"{v / 1024 ** 3:0.2f} GB"


def fmt_duration(seconds: float) -> str:
    seconds = int(max(0, seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return tr("duration.hm", h=h, m=m)
    if m:
        return tr("duration.ms", m=m, s=s)
    return tr("duration.s", s=s)


def fmt_time(ts: float) -> str:
    try:
        return time.strftime("%H:%M:%S", time.localtime(ts))
    except Exception:
        return "—"


def short_path(path: str, max_len: int = 64) -> str:
    if not path:
        return ""
    if len(path) <= max_len:
        return path
    return "…" + path[-(max_len - 1):]


KNOWN_NAMES = {
    "waterfox": "Waterfox",
    "librewolf": "LibreWolf",
    "firefox": "Firefox",
    "google-chrome": "Google Chrome",
    "chromium": "Chromium",
    "chrome": "Chrome",
    "opera": "Opera",
    "brave": "Brave",
    "thunderbird": "Thunderbird",
    "telegram": "Telegram",
    "discord": "Discord",
    "spotify": "Spotify",
    "steam": "Steam",
    "networkmanager": "NetworkManager",
    "apt": "APT",
    "dnf": "DNF",
    "pacman": "Pacman",
    "curl": "curl",
    "wget": "wget",
    "ssh": "SSH",
}


def pretty_name(comm: str, exe: str, cmdline: str = "") -> str:
    """اسم عرض واضح للعملية مع مطابقة كلمات كاملة لتفادي الالتباس."""
    base = os.path.basename(exe) if exe else ""
    haystacks = [comm or "", base, cmdline or ""]
    lowered = [h.lower() for h in haystacks]
    for key in sorted(KNOWN_NAMES, key=len, reverse=True):
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])")
        if any(pattern.search(h) for h in lowered):
            return KNOWN_NAMES[key]
    return comm or base or "—"
