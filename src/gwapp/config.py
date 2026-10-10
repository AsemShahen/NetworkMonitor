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

CONFIG_DIR = xdg_config / "glasswire"
DATA_DIR = xdg_data / "glasswire"
CACHE_DIR = xdg_cache / "glasswire"

CONFIG_FILE = CONFIG_DIR / "config.json"
BLOCKLIST_FILE = DATA_DIR / "blocklist.json"
TOTALS_FILE = DATA_DIR / "totals.json"

ENGINES = ("auto", "helper", "user", "demo")
ENGINE_LABELS = {
    "auto": "تلقائي (المساعد المميز أولاً)",
    "helper": "المساعد المميز (pkexec/نواة)",
    "user": "صلاحيات المستخدم فقط",
    "demo": "وضع تجريبي (بيانات مدمجة)",
}


def _atomic_write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class ConfigStore:
    """إعدادات قابلة للحفظ في ~/.config/glasswire/config.json."""

    DEFAULTS = {
        "refresh_ms": 1000,
        "engine": "auto",
        "unit_auto": True,
        "keep_totals": True,
        "autostart": False,
        "first_run": True,
        "confirm_block": True,
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
    target = autostart / "glasswire.desktop"
    if not enabled:
        if target.exists():
            target.unlink()
        return ""
    autostart.mkdir(parents=True, exist_ok=True)
    desktop = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        'Name=مراقب الشبكة\n'
        f"Exec={Path.home()}/.local/bin/glasswire\n"
        "X-GNOME-Autostart-enabled=true\n"
    )
    target.write_text(desktop, encoding="utf-8")
    return str(target)