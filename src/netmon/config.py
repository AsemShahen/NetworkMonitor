from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .models import BlockEntry

try:
    xdg_config = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    xdg_cache = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
except Exception:
    xdg_config = Path.home() / ".config"
    xdg_data = Path.home() / ".local" / "share"
    xdg_cache = Path.home() / ".cache"

CONFIG_DIR = xdg_config / "network-monitor"
DATA_DIR = xdg_data / "network-monitor"
CACHE_DIR = xdg_cache / "network-monitor"

REFRESH_CHOICES = [5000, 10000, 30000, 60000, 300000]

CONFIG_FILE = CONFIG_DIR / "config.json"
BLOCKLIST_FILE = DATA_DIR / "blocklist.json"
TOTALS_FILE = DATA_DIR / "totals.json"
USAGE_DB = DATA_DIR / "usage.db"
COLLECTOR_STATUS_FILE = DATA_DIR / "collector.json"


def _atomic_write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class ConfigStore:
    """إعدادات قابلة للحفظ في ~/.config/network-monitor/config.json."""

    DEFAULTS = {
        "language": "en",
        "theme": "system",
        "refresh_ms": 30000,
        "engine": "auto",
        "unit_auto": True,
        "keep_totals": True,
        "show_idle": False,
        "apply_on_start": False,
        "autostart": False,
        "minimize_to_tray": False,
        "keep_usage": True,
        "background_collector": False,
        "collector_interval_ms": 5000,
        "group_cgroups": True,
        "recent_seconds": 300,
        "usage_retention_months": 24,
        "usage_retention_days": 90,
        "first_run": True,
        "confirm_block": True,
        "security_enabled": True,
        "security_path_check": True,
        "security_mining_check": True,
        "security_upload_check": True,
        "security_spike_mbps": 5.0,
        "security_spike_ratio": 4.0,
        "security_auto_ip_check": False,
        "security_ip_provider": "abuseipdb",
        "security_abuseipdb_key": "",
        "security_virustotal_key": "",
        "security_hash_provider": "malwarebazaar",
        "security_retention_minutes": 15,
    }

    def __init__(self, path: Path = CONFIG_FILE):
        self.path = path
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.data.update(loaded)
            except Exception:
                pass
        if self.data.get("language") not in ("en", "ar"):
            self.data["language"] = "en"
        if self.data.get("theme") not in ("system", "light", "dark"):
            self.data["theme"] = "system"
        valid = set(REFRESH_CHOICES)
        try:
            if int(self.data.get("refresh_ms", 30000)) not in valid:
                self.data["refresh_ms"] = 30000
        except (TypeError, ValueError):
            self.data["refresh_ms"] = 30000
        try:
            interval = int(self.data.get("collector_interval_ms", 5000))
        except (TypeError, ValueError):
            interval = 5000
        self.data["collector_interval_ms"] = max(1000, min(60000, interval))

        if self.data.get("security_ip_provider") not in ("abuseipdb", "virustotal"):
            self.data["security_ip_provider"] = "abuseipdb"
        if self.data.get("security_hash_provider") not in ("malwarebazaar", "virustotal"):
            self.data["security_hash_provider"] = "malwarebazaar"
        try:
            self.data["security_spike_mbps"] = max(
                0.1, min(100000.0, float(self.data.get("security_spike_mbps", 5.0)))
            )
        except (TypeError, ValueError):
            self.data["security_spike_mbps"] = 5.0
        try:
            self.data["security_spike_ratio"] = max(
                1.0, min(1000.0, float(self.data.get("security_spike_ratio", 4.0)))
            )
        except (TypeError, ValueError):
            self.data["security_spike_ratio"] = 4.0
        try:
            self.data["security_retention_minutes"] = max(
                1, min(1440, int(self.data.get("security_retention_minutes", 15)))
            )
        except (TypeError, ValueError):
            self.data["security_retention_minutes"] = 15

    def save(self) -> None:
        _atomic_write(self.path, self.data)

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value
        self.save()


class BlocklistStore:
    """قائمة الحظر مع استيراد/تصدير كنسخة احتياطية."""

    def __init__(self, path: Path = BLOCKLIST_FILE):
        self.path = path
        self.entries: dict[str, BlockEntry] = {}
        self.load()

    def load(self) -> None:
        self.entries = {}
        if not self.path.exists():
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw:
                if isinstance(item, dict) and item.get("slug"):
                    entry = BlockEntry.from_dict(item)
                    self.entries[entry.slug] = entry
        except Exception:
            pass

    def save(self) -> None:
        _atomic_write(self.path, [e.to_dict() for e in self.entries.values()])

    def add(self, entry: BlockEntry) -> None:
        self.entries[entry.slug] = entry
        self.save()

    def remove(self, slug: str) -> bool:
        if slug in self.entries:
            del self.entries[slug]
            self.save()
            return True
        return False

    def list(self) -> list[BlockEntry]:
        return sorted(self.entries.values(), key=lambda e: e.exe)

    def has(self, slug: str) -> bool:
        return slug in self.entries

    def export_to(self, path: Path) -> None:
        _atomic_write(path, [e.to_dict() for e in self.entries.values()])

    def import_from(self, path: Path) -> int:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        count = 0
        for item in raw:
            if isinstance(item, dict) and item.get("slug"):
                self.entries[item["slug"]] = BlockEntry.from_dict(item)
                count += 1
        self.save()
        return count


class TotalsStore:
    """إجماليات تراكمية لكل مسار تنفيذي، تُحفظ للاستعادة عند الإقلاع."""

    def __init__(self, path: Path = TOTALS_FILE):
        self.path = path
        self.totals: dict[str, dict] = {}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                with open(self.path, encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    self.totals = raw
            except Exception:
                pass

    def save(self) -> None:
        _atomic_write(self.path, self.totals)

    def add(self, exe: str, down: int, up: int) -> None:
        if not exe:
            return
        rec = self.totals.setdefault(exe, {"down": 0, "up": 0})
        rec["down"] = rec.get("down", 0) + down
        rec["up"] = rec.get("up", 0) + up
        rec["name"] = Path(exe).name

    def get(self, exe: str) -> tuple[int, int]:
        rec = self.totals.get(exe)
        if not rec:
            return 0, 0
        return rec.get("down", 0), rec.get("up", 0)

    def reset(self) -> None:
        self.totals = {}
        self.save()


def slugify(exe: str) -> str:
    """تحويل مسار تنفيذي إلى معرف آمن لأسماء cgroup وقواعد nft."""
    if not exe:
        return "unknown"
    base = os.path.basename(exe.rstrip("/")) or "unknown"
    safe = "".join(ch if (ch.isalnum() or ch in "._-") else "_" for ch in base)
    safe = safe.strip("._-") or "unknown"
    return safe[:40]


def install_autostart(enabled: bool) -> str:
    """إنشاء/حذف تشغيل تلقائي في ~/.config/autostart."""
    autostart = Path.home() / ".config" / "autostart"
    target = autostart / "network-monitor.desktop"
    if not enabled:
        if target.exists():
            target.unlink()
        return ""
    autostart.mkdir(parents=True, exist_ok=True)
    import shutil as _sh

    candidates = (
        os.environ.get("APPIMAGE"),
        _sh.which("network-monitor"),
        str(Path(__file__).resolve().parents[2] / "network-monitor"),
    )
    exe = next((value for value in candidates if value and Path(value).is_file()), "")
    if not exe:
        exe = str(Path.home() / ".local" / "bin" / "network-monitor")
    exec_path = '"' + exe.replace("\\", "\\\\").replace('"', '\\"') + '"'
    desktop = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        'Name=Network Monitor\n'
        'Name[ar]=مراقب الشبكة\n'
        f"Exec={exec_path} --hidden\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
    target.write_text(desktop, encoding="utf-8")
    return str(target)