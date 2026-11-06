from __future__ import annotations

"""Install and control the systemd user service for background collection.

The unit is generated at runtime instead of shipped as a static file because
the correct command differs between a Debian/RPM installation, a manual
``/opt`` installation, and an AppImage that can live anywhere.  Everything is
installed under the current user's home directory; no root access is needed.
"""

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .config import CONFIG_DIR, DATA_DIR
from .updater import flatpak_id

UNIT_NAME = "network-monitor-collector.service"
UNIT_PATH = CONFIG_DIR.parent / "systemd" / "user" / UNIT_NAME
WRAPPER_PATH = DATA_DIR / "collector-launcher.sh"


class CollectorServiceError(RuntimeError):
    pass


def _appimage() -> str:
    value = os.environ.get("APPIMAGE") or ""
    if value:
        try:
            return str(Path(value).resolve())
        except OSError:
            pass
    return ""


def _launcher_command() -> list[str]:
    appimage = _appimage()
    if appimage and Path(appimage).is_file():
        return [appimage, "--collector"]
    if Path("/.flatpak-info").exists():
        return ["flatpak", "run", flatpak_id(), "--collector"]

    candidates = [
        "/usr/bin/network-monitor",
        "/usr/local/bin/network-monitor",
        "/opt/network-monitor/network-monitor",
        shutil.which("network-monitor") or "",
        str(Path(__file__).resolve().parents[2] / "network-monitor"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return [candidate, "--collector"]
    return [sys.executable, "-m", "netmon", "--collector"]


def _systemd_quote(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    systemctl = shutil.which("systemctl")
    if not systemctl:
        raise CollectorServiceError("systemctl is not available")
    try:
        proc = subprocess.run(
            [systemctl, "--user", *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CollectorServiceError(str(exc)) from exc
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise CollectorServiceError(detail or f"systemctl exited with code {proc.returncode}")
    return proc


def available() -> bool:
    """Return whether a usable systemd user manager is likely present."""
    if not shutil.which("systemctl"):
        return False
    return bool(os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("DBUS_SESSION_BUS_ADDRESS"))


def install_unit() -> Path:
    UNIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    WRAPPER_PATH.parent.mkdir(parents=True, exist_ok=True)
    command = _launcher_command()
    WRAPPER_PATH.write_text(
        "#!/bin/sh\nset -e\nexec " + shlex.join(command) + "\n",
        encoding="utf-8",
    )
    WRAPPER_PATH.chmod(0o755)

    environment = [
        "Environment=PYTHONUNBUFFERED=1",
        "Environment=" + _systemd_quote("XDG_CONFIG_HOME=" + str(CONFIG_DIR.parent)),
        "Environment=" + _systemd_quote("XDG_DATA_HOME=" + str(DATA_DIR.parent)),
    ]
    unit = "\n".join(
        [
            "[Unit]",
            "Description=Network Monitor background usage collector",
            "After=graphical-session.target",
            "PartOf=graphical-session.target",
            "",
            "[Service]",
            "Type=simple",
            "ExecStart=" + _systemd_quote(str(WRAPPER_PATH)),
            "Restart=on-failure",
            "RestartSec=5",
            "Nice=10",
            "IOSchedulingClass=idle",
            "NoNewPrivileges=true",
            *environment,
            "",
            "[Install]",
            "WantedBy=default.target",
            "",
        ]
    )
    UNIT_PATH.write_text(unit, encoding="utf-8")
    try:
        _systemctl("daemon-reload")
    except CollectorServiceError:
        # The unit is still written; enable will report the real problem.
        pass
    return UNIT_PATH


def enable() -> None:
    install_unit()
    _systemctl("enable", "--now", UNIT_NAME)


def disable() -> None:
    # Keep the unit file installed so the user can enable it again quickly.
    _systemctl("disable", "--now", UNIT_NAME, check=False)
    _systemctl("stop", UNIT_NAME, check=False)


def restart() -> None:
    install_unit()
    _systemctl("restart", UNIT_NAME)


def uninstall_unit() -> None:
    try:
        _systemctl("disable", "--now", UNIT_NAME, check=False)
    finally:
        for path in (UNIT_PATH, WRAPPER_PATH):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        try:
            _systemctl("daemon-reload", check=False)
        except CollectorServiceError:
            pass
