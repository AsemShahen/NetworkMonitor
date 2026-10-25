#!/usr/bin/env bash
# Build a self-contained AppImage with Python, PySide6 and pyqtgraph.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
VERSION="${VERSION:-$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/src/netmon/__init__.py")}"
RUNTIME="$BUILD_DIR/runtime"
APPDIR="$BUILD_DIR/AppDir"
TOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"
OUT="$BUILD_DIR/NetworkMonitor-${VERSION}-x86_64.AppImage"

if [ ! -x "$RUNTIME/bin/python3" ]; then
    "$ROOT/packaging/build-runtime.sh"
fi

command -v curl >/dev/null 2>&1 || { echo "curl is required" >&2; exit 1; }

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr" "$APPDIR/usr/share/network-monitor" "$APPDIR/usr/libexec/network-monitor"
cp -a "$RUNTIME/." "$APPDIR/usr/"
cp -a "$ROOT/src" "$APPDIR/usr/share/network-monitor/src"
cp -a "$ROOT/LICENSE" "$APPDIR/usr/share/network-monitor/LICENSE"

find "$APPDIR/usr/share/network-monitor" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$APPDIR/usr/share/network-monitor" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

install -Dm755 "$ROOT/bin/network-monitor-helper" \
    "$APPDIR/usr/libexec/network-monitor/network-monitor-helper"
install -Dm644 "$ROOT/data/network-monitor-256.png" "$APPDIR/network-monitor.png"
cp "$APPDIR/network-monitor.png" "$APPDIR/.DirIcon"
install -Dm644 "$ROOT/packaging/appimage/network-monitor.desktop" "$APPDIR/network-monitor.desktop"
install -Dm755 "$ROOT/packaging/appimage/AppRun" "$APPDIR/AppRun"

if [ ! -x "$TOOL" ]; then
    curl -fL --retry 3 \
        "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -o "$TOOL"
    chmod +x "$TOOL"
fi

ARCH=x86_64 "$TOOL" --appimage-extract-and-run --no-appstream "$APPDIR" "$OUT"
chmod +x "$OUT"
echo "Built: $OUT"
