from __future__ import annotations

"""In-app update support for Network Monitor.

The updater deliberately keeps the trust model simple:

* release metadata comes from the official GitHub Releases API;
* every downloaded asset is checked against the release ``SHA256SUMS``;
* ``SHA256SUMS`` must have a valid detached GPG signature made by the key
  embedded in the application;
* the installer only runs after both checks succeed.

The module has no Qt dependency so it can be tested headlessly.  The GUI runs
these functions in a worker thread.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from . import APP_ID, __version__
from .i18n import tr

REPOSITORY = "AsemShahen/NetworkMonitor"
RELEASES_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPOSITORY}/releases"
MANUAL_TARGET = Path("/opt/network-monitor")
EXPECTED_FINGERPRINT = "D53CB321C38875CCA82128CC77EED1C545319AE8"
PUBLIC_KEY_PATH = Path(__file__).resolve().parent / "resources" / "network-monitor-public.asc"

ProgressCallback = Callable[[str, int | None], None]


class UpdateError(RuntimeError):
    """A user-presentable update failure."""


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    size: int = 0


@dataclass
class UpdateInfo:
    version: str
    tag: str
    page_url: str
    notes: str
    install_type: str
    asset: ReleaseAsset | None = None
    checksums: ReleaseAsset | None = None
    signature: ReleaseAsset | None = None
    assets: dict[str, ReleaseAsset] = field(default_factory=dict)


def normalize_version(value: str) -> str:
    return str(value or "").strip().lstrip("vV")


def version_tuple(value: str) -> tuple[int, ...]:
    numbers = re.findall(r"\d+", normalize_version(value))
    return tuple(int(piece) for piece in numbers[:4]) or (0,)


def is_newer(latest: str, current: str) -> bool:
    return version_tuple(latest) > version_tuple(current)


def parse_checksums(text: str) -> dict[str, str]:
    """Parse ``sha256sum`` output, including the optional ``*`` marker."""

    checksums: dict[str, str] = {}
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        digest, name = parts[0].lower(), parts[-1].lstrip("*")
        if re.fullmatch(r"[0-9a-f]{64}", digest) and name:
            checksums[name] = digest
    return checksums


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _command_ok(command: list[str]) -> bool:
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _dpkg_installed() -> bool:
    if not shutil.which("dpkg-query"):
        return False
    try:
        proc = subprocess.run(
            ["dpkg-query", "-W", "-f=${Status}", "network-monitor"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and "install ok installed" in (proc.stdout or "")


def _rpm_installed() -> bool:
    if not shutil.which("rpm"):
        return False
    return _command_ok(["rpm", "-q", "network-monitor"])


def detect_install_type(env: dict[str, str] | None = None) -> str:
    """Return one of flatpak/appimage/deb/rpm/manual/source."""

    environment = env if env is not None else os.environ
    in_flatpak = bool(environment.get("FLATPAK_ID"))
    if not in_flatpak and env is None:
        in_flatpak = Path("/.flatpak-info").exists()
    if in_flatpak:
        return "flatpak"

    appimage = environment.get("APPIMAGE") or ""
    if not appimage and sys.argv:
        candidate = sys.argv[0] or ""
        if candidate.endswith(".AppImage"):
            appimage = candidate
    if appimage:
        return "appimage"

    if _dpkg_installed():
        return "deb"
    if _rpm_installed():
        return "rpm"
    if MANUAL_TARGET.is_dir():
        return "manual"
    return "source"


def current_appimage_path(env: dict[str, str] | None = None) -> Path:
    environment = env if env is not None else os.environ
    raw = environment.get("APPIMAGE") or ""
    if not raw and sys.argv and (sys.argv[0] or "").endswith(".AppImage"):
        raw = sys.argv[0]
    if not raw:
        raise UpdateError(tr("update.error.appimage_path"))
    path = Path(raw).expanduser()
    try:
        return path.resolve()
    except OSError:
        return path.absolute()


def flatpak_id(env: dict[str, str] | None = None) -> str:
    environment = env if env is not None else os.environ
    value = environment.get("FLATPAK_ID") or ""
    if value:
        return value
    try:
        text = Path("/.flatpak-info").read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    for line in text.splitlines():
        if line.startswith("name="):
            return line.split("=", 1)[1].strip()
    return APP_ID


def _asset_from_json(item: dict) -> ReleaseAsset | None:
    name = str(item.get("name") or "")
    url = str(item.get("browser_download_url") or "")
    if not name or not url:
        return None
    try:
        size = int(item.get("size") or 0)
    except (TypeError, ValueError):
        size = 0
    return ReleaseAsset(name=name, url=url, size=size)


def select_asset(
    assets: dict[str, ReleaseAsset], version: str, install_type: str
) -> ReleaseAsset | None:
    version = normalize_version(version)
    candidates: list[str] = []
    if install_type == "manual":
        candidates = [
            name
            for name in assets
            if name.startswith(f"NetworkMonitor-{version}-linux-")
            and name.endswith(".tar.gz")
        ]
    elif install_type == "appimage":
        candidates = [
            name
            for name in assets
            if name.startswith(f"NetworkMonitor-{version}-")
            and name.endswith(".AppImage")
            and not name.endswith(".zsync")
        ]
    elif install_type == "deb":
        candidates = [
            name
            for name in assets
            if name.startswith(f"network-monitor_{version}_") and name.endswith(".deb")
        ]
    elif install_type == "rpm":
        candidates = [
            name
            for name in assets
            if name.startswith(f"network-monitor-{version}-")
            and name.endswith(".rpm")
            and not name.endswith(".src.rpm")
        ]
    elif install_type == "flatpak":
        candidates = [
            name
            for name in assets
            if name.startswith(f"NetworkMonitor-{version}-") and name.endswith(".flatpak")
        ]
    if not candidates:
        return None
    return assets[sorted(candidates)[0]]


def _release_assets(release: dict) -> dict[str, ReleaseAsset]:
    result: dict[str, ReleaseAsset] = {}
    for item in release.get("assets") or []:
        if not isinstance(item, dict):
            continue
        asset = _asset_from_json(item)
        if asset is not None:
            result[asset.name] = asset
    return result


def _fetch_release(timeout: float = 25.0) -> dict:
    request = Request(
        RELEASES_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"NetworkMonitor/{__version__}",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except HTTPError as exc:
        raise UpdateError(tr("update.error.http", code=exc.code)) from exc
    except URLError as exc:
        raise UpdateError(tr("update.error.network", message=str(exc.reason))) from exc
    except OSError as exc:
        raise UpdateError(tr("update.error.network", message=str(exc))) from exc
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise UpdateError(tr("update.error.release")) from exc
    if not isinstance(data, dict):
        raise UpdateError(tr("update.error.release"))
    return data


def check_for_update(
    current_version: str | None = None,
    install_type: str | None = None,
    release: dict | None = None,
) -> UpdateInfo | None:
    """Return update information, or ``None`` when the installed copy is current."""

    current = normalize_version(current_version or __version__)
    kind = install_type or detect_install_type()
    if kind == "source":
        raise UpdateError(tr("update.error.unsupported"))

    data = release if release is not None else _fetch_release()
    tag = str(data.get("tag_name") or data.get("name") or "")
    latest = normalize_version(tag)
    if not latest or not is_newer(latest, current):
        return None

    assets = _release_assets(data)
    asset = select_asset(assets, latest, kind)
    if kind != "flatpak" and asset is None:
        raise UpdateError(
            tr(
                "update.error.asset",
                version=latest,
                type=tr(f"update.type.{kind}"),
            )
        )
    if kind != "flatpak" and (
        assets.get("SHA256SUMS") is None or assets.get("SHA256SUMS.asc") is None
    ):
        raise UpdateError(tr("update.error.signature_missing"))

    return UpdateInfo(
        version=latest,
        tag=tag or f"v{latest}",
        page_url=str(data.get("html_url") or f"{RELEASES_PAGE}/tag/v{latest}"),
        notes=str(data.get("body") or ""),
        install_type=kind,
        asset=asset,
        checksums=assets.get("SHA256SUMS"),
        signature=assets.get("SHA256SUMS.asc"),
        assets=assets,
    )


def _report(progress: ProgressCallback | None, message: str, percent: int | None = None) -> None:
    if progress is not None:
        progress(message, percent)


def _download(
    asset: ReleaseAsset,
    destination: Path,
    progress: ProgressCallback | None = None,
    label: str = "",
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        asset.url,
        headers={"User-Agent": f"NetworkMonitor/{__version__}"},
    )
    try:
        with urlopen(request, timeout=60) as response, open(destination, "wb") as handle:
            try:
                total = int(response.headers.get("Content-Length") or asset.size or 0)
            except (TypeError, ValueError):
                total = 0
            received = 0
            if label:
                _report(progress, label, 0 if total else None)
            while True:
                chunk = response.read(1024 * 128)
                if not chunk:
                    break
                handle.write(chunk)
                received += len(chunk)
                if label and total > 0:
                    _report(progress, label, min(100, int(received * 100 / total)))
    except HTTPError as exc:
        raise UpdateError(tr("update.error.http", code=exc.code)) from exc
    except (URLError, OSError) as exc:
        raise UpdateError(tr("update.error.network", message=str(exc))) from exc
    return destination


def _key_fingerprints(gpg: str, environment: dict[str, str]) -> set[str]:
    proc = subprocess.run(
        [gpg, "--batch", "--with-colons", "--list-keys"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env=environment,
        timeout=20,
    )
    fingerprints: set[str] = set()
    for line in (proc.stdout or "").splitlines():
        if line.startswith("fpr:"):
            fields = line.split(":")
            if len(fields) > 9 and fields[9]:
                fingerprints.add(fields[9].upper())
    return fingerprints


def verify_checksums(checksums_path: Path, signature_path: Path) -> None:
    """Verify ``SHA256SUMS.asc`` using the embedded public key."""

    if not PUBLIC_KEY_PATH.is_file():
        raise UpdateError(tr("update.error.public_key"))
    gpg = shutil.which("gpg")
    if not gpg:
        raise UpdateError(tr("update.error.gpg_missing"))

    try:
        with tempfile.TemporaryDirectory(prefix="network-monitor-gpg-") as home:
            gnupg = Path(home)
            gnupg.chmod(0o700)
            environment = os.environ.copy()
            environment["GNUPGHOME"] = str(gnupg)
            environment["LC_ALL"] = "C"

            imported = subprocess.run(
                [gpg, "--batch", "--import", str(PUBLIC_KEY_PATH)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
                timeout=30,
            )
            if imported.returncode != 0:
                raise UpdateError(tr("update.error.signature"))

            fingerprints = _key_fingerprints(gpg, environment)
            if EXPECTED_FINGERPRINT not in fingerprints:
                raise UpdateError(tr("update.error.signature"))

            verified = subprocess.run(
                [
                    gpg,
                    "--batch",
                    "--status-fd=1",
                    "--verify",
                    str(signature_path),
                    str(checksums_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
                timeout=30,
            )
            if verified.returncode != 0:
                raise UpdateError(tr("update.error.signature"))
            valid = False
            for line in (verified.stdout or "").splitlines():
                if line.startswith("[GNUPG:] VALIDSIG "):
                    fields = line.split()
                    if len(fields) >= 3 and fields[2].upper() in fingerprints:
                        valid = True
                        break
            if not valid:
                raise UpdateError(tr("update.error.signature"))
    except UpdateError:
        raise
    except (OSError, subprocess.SubprocessError) as exc:
        raise UpdateError(tr("update.error.signature")) from exc


def _run_privileged(command: list[str], timeout: float = 900.0) -> str:
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise UpdateError(tr("update.error.command", code=-1, detail=str(exc))) from exc
    output = (proc.stdout or "").strip()
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        if len(detail) > 1200:
            detail = detail[-1200:]
        raise UpdateError(
            tr("update.error.command", code=proc.returncode, detail=detail or "—")
        )
    return output


MANUAL_INSTALL_SCRIPT = r"""#!/bin/sh
set -eu

TARBALL="$1"
TARGET="$2"
BACKUP="$3"
STAGE="$4"
VERSION="$5"

rm -rf "$STAGE"
mkdir -p "$STAGE"
tar -xzf "$TARBALL" -C "$STAGE"
SRC="$STAGE/network-monitor"
if [ ! -x "$SRC/network-monitor" ] || [ ! -x "$SRC/runtime/bin/python3" ]; then
    echo "The downloaded archive is not a valid Network Monitor installation." >&2
    exit 2
fi

INSTALLED=0
TARGET_EXISTED=0
TARGET_BACKED_UP=0
cleanup() {
    if [ "$INSTALLED" -eq 0 ]; then
        if [ "$TARGET_BACKED_UP" -eq 1 ]; then
            rm -rf "$TARGET"
            if [ -d "$BACKUP" ]; then
                mv "$BACKUP" "$TARGET"
            fi
        elif [ "$TARGET_EXISTED" -eq 0 ]; then
            rm -rf "$TARGET"
        fi
    fi
    rm -rf "$STAGE"
}
trap cleanup EXIT INT TERM

if [ -d "$TARGET" ]; then
    TARGET_EXISTED=1
    rm -rf "$BACKUP"
    mv "$TARGET" "$BACKUP"
    TARGET_BACKED_UP=1
fi
mv "$SRC" "$TARGET"
chown -R root:root "$TARGET"
chmod 755 "$TARGET/network-monitor"

install -Dm755 "$TARGET/bin/network-monitor-helper" \
    /usr/libexec/network-monitor/network-monitor-helper || true
install -Dm644 "$TARGET/data/org.networkmonitor.helper.policy" \
    /usr/share/polkit-1/actions/org.networkmonitor.helper.policy || true
install -Dm644 "$TARGET/data/network-monitor.desktop" \
    /usr/share/applications/network-monitor.desktop || true
install -Dm644 "$TARGET/data/network-monitor.metainfo.xml" \
    /usr/share/metainfo/network-monitor.metainfo.xml || true
for SIZE in 64 128 256 512; do
    install -Dm644 "$TARGET/data/network-monitor-${SIZE}.png" \
        "/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/network-monitor.png" || true
done
install -Dm644 "$TARGET/data/network-monitor.svg" \
    /usr/share/icons/hicolor/scalable/apps/network-monitor.svg || true

cat > /usr/local/bin/network-monitor <<'WRAP'
#!/bin/sh
exec /opt/network-monitor/network-monitor "$@"
WRAP
chmod 755 /usr/local/bin/network-monitor

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

INSTALLED=1
trap - EXIT INT TERM
rm -rf "$STAGE"
echo "Installed Network Monitor $VERSION in $TARGET"
"""


def _install_manual(archive: Path, version: str, workdir: Path) -> str:
    if not shutil.which("pkexec"):
        raise UpdateError(tr("update.error.pkexec_missing"))
    if not shutil.which("tar"):
        raise UpdateError(tr("update.error.manual_missing"))

    script = workdir / "install-manual.sh"
    script.write_text(MANUAL_INSTALL_SCRIPT, encoding="utf-8")
    script.chmod(0o700)
    stage = workdir / "manual-stage"
    backup = Path("/opt") / (
        f"network-monitor.backup-{version}-{time.strftime('%Y%m%d-%H%M%S')}"
    )
    _run_privileged(
        [
            "pkexec",
            "/bin/sh",
            str(script),
            str(archive),
            str(MANUAL_TARGET),
            str(backup),
            str(stage),
            version,
        ],
        timeout=900.0,
    )
    return tr(
        "update.installed_manual",
        version=version,
        path=str(MANUAL_TARGET),
    )


def _install_appimage(archive: Path, version: str) -> str:
    target = current_appimage_path()
    if not target.is_file():
        raise UpdateError(tr("update.error.appimage_missing", path=str(target)))
    temporary = target.parent / f".{target.name}.new-{os.getpid()}"
    try:
        shutil.copyfile(archive, temporary)
        mode = target.stat().st_mode
        temporary.chmod(mode | 0o111)
        os.replace(temporary, target)
    except PermissionError as exc:
        raise UpdateError(tr("update.error.appimage_perm", path=str(target))) from exc
    except OSError as exc:
        raise UpdateError(tr("update.error.command", code=-1, detail=str(exc))) from exc
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass
    return tr("update.installed_appimage", version=version, path=str(target))


def _install_deb(archive: Path, version: str) -> str:
    if not shutil.which("pkexec"):
        raise UpdateError(tr("update.error.pkexec_missing"))
    if shutil.which("apt-get"):
        command = [
            "pkexec",
            "env",
            "DEBIAN_FRONTEND=noninteractive",
            "apt-get",
            "install",
            "-y",
            str(archive),
        ]
    elif shutil.which("dpkg"):
        command = ["pkexec", "dpkg", "-i", str(archive)]
    else:
        raise UpdateError(tr("update.error.unsupported"))
    _run_privileged(command)
    return tr("update.installed_deb", version=version)


def _install_rpm(archive: Path, version: str) -> str:
    if not shutil.which("pkexec"):
        raise UpdateError(tr("update.error.pkexec_missing"))
    if shutil.which("dnf"):
        command = ["pkexec", "dnf", "install", "-y", "--nogpgcheck", str(archive)]
    elif shutil.which("rpm"):
        command = ["pkexec", "rpm", "-U", "--replacepkgs", str(archive)]
    else:
        raise UpdateError(tr("update.error.unsupported"))
    _run_privileged(command)
    return tr("update.installed_rpm", version=version)


def _install_flatpak(version: str) -> str:
    app_id = flatpak_id()
    if Path("/.flatpak-info").exists() and shutil.which("flatpak-spawn"):
        command = ["flatpak-spawn", "--host", "flatpak", "update", "-y", app_id]
    elif shutil.which("flatpak"):
        command = ["flatpak", "update", "-y", app_id]
    else:
        raise UpdateError(tr("update.error.unsupported"))
    _run_privileged(command)
    return tr("update.installed_flatpak", version=version)


def download_and_install(
    info: UpdateInfo,
    progress: ProgressCallback | None = None,
) -> str:
    """Download, verify, and install an update; return a user-facing message."""

    kind = info.install_type
    if kind == "flatpak":
        _report(progress, tr("update.installing"))
        return _install_flatpak(info.version)

    if info.checksums is None or info.signature is None:
        raise UpdateError(tr("update.error.signature_missing"))
    if info.asset is None:
        raise UpdateError(
            tr("update.error.asset", version=info.version, type=tr(f"update.type.{kind}"))
        )

    workdir = Path(tempfile.mkdtemp(prefix="network-monitor-update-"))
    try:
        checksums_path = _download(
            info.checksums,
            workdir / "SHA256SUMS",
            progress,
            tr("update.downloading_checksums"),
        )
        signature_path = _download(
            info.signature,
            workdir / "SHA256SUMS.asc",
            progress,
            tr("update.downloading_checksums"),
        )
        _report(progress, tr("update.verifying"))
        verify_checksums(checksums_path, signature_path)
        expected = parse_checksums(
            checksums_path.read_text(encoding="utf-8", errors="replace")
        ).get(info.asset.name)
        if not expected:
            raise UpdateError(tr("update.error.checksum", name=info.asset.name))

        archive = _download(
            info.asset,
            workdir / info.asset.name,
            progress,
            tr("update.downloading", name=info.asset.name),
        )
        _report(progress, tr("update.verifying"))
        if sha256_file(archive) != expected:
            raise UpdateError(tr("update.error.checksum", name=info.asset.name))

        _report(progress, tr("update.installing"))
        if kind == "manual":
            return _install_manual(archive, info.version, workdir)
        if kind == "appimage":
            return _install_appimage(archive, info.version)
        if kind == "deb":
            return _install_deb(archive, info.version)
        if kind == "rpm":
            return _install_rpm(archive, info.version)
        raise UpdateError(tr("update.error.unsupported"))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
