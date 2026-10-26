#!/usr/bin/env bash
# Build a Debian package with a self-contained Python/PySide6 runtime.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
VERSION="${VERSION:-$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/src/netmon/__init__.py")}"
ARCH="${ARCH:-amd64}"
RUNTIME="$BUILD_DIR/runtime"
PKG="$BUILD_DIR/deb/network-monitor_${VERSION}_${ARCH}"
OUT="$BUILD_DIR/network-monitor_${VERSION}_${ARCH}.deb"

if [ ! -x "$RUNTIME/bin/python3" ]; then
    "$ROOT/packaging/build-runtime.sh"
fi

command -v dpkg-deb >/dev/null 2>&1 || { echo "dpkg-deb is required" >&2; exit 1; }

rm -rf "$PKG"
mkdir -p \
    "$PKG/DEBIAN" \
    "$PKG/opt/network-monitor" \
    "$PKG/usr/bin" \
    "$PKG/usr/libexec/network-monitor" \
    "$PKG/usr/share/applications" \
    "$PKG/usr/share/metainfo" \
    "$PKG/usr/share/polkit-1/actions" \
    "$PKG/usr/share/doc/network-monitor" \
    "$PKG/usr/share/licenses/network-monitor"

cp -a "$RUNTIME" "$PKG/opt/network-monitor/runtime"
cp -a "$ROOT/src" "$PKG/opt/network-monitor/src"

# Do not ship developer launchers or bytecode compiled by another Python.
find "$PKG/opt/network-monitor" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$PKG/opt/network-monitor" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

install -Dm755 "$ROOT/bin/network-monitor-helper" \
    "$PKG/usr/libexec/network-monitor/network-monitor-helper"
install -Dm644 "$ROOT/data/network-monitor.desktop" \
    "$PKG/usr/share/applications/network-monitor.desktop"
install -Dm644 "$ROOT/data/network-monitor.metainfo.xml" \
    "$PKG/usr/share/metainfo/network-monitor.metainfo.xml"
install -Dm644 "$ROOT/data/org.networkmonitor.helper.policy" \
    "$PKG/usr/share/polkit-1/actions/org.networkmonitor.helper.policy"
install -Dm644 "$ROOT/LICENSE" "$PKG/usr/share/doc/network-monitor/copyright"
install -Dm644 "$ROOT/LICENSE" "$PKG/usr/share/licenses/network-monitor/LICENSE"

for size in 64 128 256 512; do
    install -Dm644 "$ROOT/data/network-monitor-${size}.png" \
        "$PKG/usr/share/icons/hicolor/${size}x${size}/apps/network-monitor.png"
done
install -Dm644 "$ROOT/data/network-monitor.svg" \
    "$PKG/usr/share/icons/hicolor/scalable/apps/network-monitor.svg"

cat > "$PKG/usr/bin/network-monitor" <<'LAUNCHER'
#!/bin/sh
export PYTHONPATH="/opt/network-monitor/src${PYTHONPATH:+:$PYTHONPATH}"
exec /opt/network-monitor/runtime/bin/python3 -m netmon "$@"
LAUNCHER
chmod 755 "$PKG/usr/bin/network-monitor"

cat > "$PKG/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
exit 0
POSTINST
chmod 755 "$PKG/DEBIAN/postinst"

cat > "$PKG/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi
exit 0
POSTRM
chmod 755 "$PKG/DEBIAN/postrm"

INSTALLED_SIZE="$(du -sk "$PKG" | cut -f1)"
cat > "$PKG/DEBIAN/control" <<CONTROL
Package: network-monitor
Version: ${VERSION}
Section: net
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_SIZE}
Maintainer: AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com>
Homepage: https://github.com/AsemShahen/NetworkMonitor
Depends: pkexec | policykit-1, nftables, iproute2, python3, libc6 (>= 2.34), libstdc++6, libgl1, libegl1, libopengl0, libxkbcommon0, libxkbcommon-x11-0, libdbus-1-3, libfontconfig1, libfreetype6, libglib2.0-0, libx11-6, libx11-xcb1, libxext6, libxrender1, libxi6, libsm6, libice6, libxcb1, libxcb-util1, libxcb-cursor0, libxcb-icccm4, libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render0, libxcb-render-util0, libxcb-shape0, libxcb-shm0, libxcb-sync1, libxcb-glx0, libxcb-dri2-0, libxcb-dri3-0, libxcb-present0, libxcb-xfixes0, libxcb-xinerama0, libxcb-xkb1
Recommends: fonts-noto-core
Description: Per-application network monitor with blocking
 Network Monitor shows live download and upload speeds for every
 application, active connections, executable paths, and session totals.
 It can block selected applications with cgroup v2 and nftables through
 a polkit-authenticated helper. The interface is available in English and
 Arabic.
CONTROL

dpkg-deb --build --root-owner-group "$PKG" "$OUT"
echo "Built: $OUT"
