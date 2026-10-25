#!/usr/bin/env bash
# Build an RPM package with a self-contained Python/PySide6 runtime.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
VERSION="${VERSION:-$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/src/netmon/__init__.py")}"
RUNTIME="$BUILD_DIR/runtime"
TOP="$BUILD_DIR/rpmbuild"
SOURCES="$TOP/SOURCES"
ROOTFS="$SOURCES/network-monitor-root"
RPMDIR="$TOP/RPMS"

if [ ! -x "$RUNTIME/bin/python3" ]; then
    "$ROOT/packaging/build-runtime.sh"
fi

command -v rpmbuild >/dev/null 2>&1 || { echo "rpmbuild is required" >&2; exit 1; }

rm -rf "$TOP"
mkdir -p "$ROOTFS/opt/network-monitor" "$ROOTFS/usr/bin" "$RPMDIR" \
    "$TOP/SPECS" "$TOP/BUILD" "$TOP/BUILDROOT" "$TOP/SRPMS"

cp -a "$RUNTIME" "$ROOTFS/opt/network-monitor/runtime"
cp -a "$ROOT/src" "$ROOTFS/opt/network-monitor/src"

# Do not ship developer launchers or bytecode compiled by another Python.
find "$ROOTFS/opt/network-monitor" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$ROOTFS/opt/network-monitor" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

install -Dm755 "$ROOT/bin/network-monitor-helper" \
    "$ROOTFS/usr/libexec/network-monitor/network-monitor-helper"
install -Dm644 "$ROOT/data/network-monitor.desktop" \
    "$ROOTFS/usr/share/applications/network-monitor.desktop"
install -Dm644 "$ROOT/data/org.networkmonitor.helper.policy" \
    "$ROOTFS/usr/share/polkit-1/actions/org.networkmonitor.helper.policy"

for size in 64 128 256 512; do
    install -Dm644 "$ROOT/data/network-monitor-${size}.png" \
        "$ROOTFS/usr/share/icons/hicolor/${size}x${size}/apps/network-monitor.png"
done
install -Dm644 "$ROOT/data/network-monitor.svg" \
    "$ROOTFS/usr/share/icons/hicolor/scalable/apps/network-monitor.svg"

cat > "$ROOTFS/usr/bin/network-monitor" <<'LAUNCHER'
#!/bin/sh
export PYTHONPATH="/opt/network-monitor/src${PYTHONPATH:+:$PYTHONPATH}"
exec /opt/network-monitor/runtime/bin/python3 -m netmon "$@"
LAUNCHER
chmod 755 "$ROOTFS/usr/bin/network-monitor"

cp "$ROOT/LICENSE" "$SOURCES/LICENSE"

rpmbuild -bb \
    --define "_version $VERSION" \
    --define "_topdir $TOP" \
    --define "_sourcedir $SOURCES" \
    --define "_rpmdir $RPMDIR" \
    --define "_builddir $TOP/BUILD" \
    --define "_buildrootdir $TOP/BUILDROOT" \
    --define "_specdir $TOP/SPECS" \
    --define "_srcrpmdir $TOP/SRPMS" \
    "$ROOT/packaging/network-monitor.spec"

RPM_FILE="$(find "$RPMDIR" -type f -name 'network-monitor-*.rpm' | head -n 1)"
if [ -z "$RPM_FILE" ]; then
    echo "rpmbuild did not produce an RPM" >&2
    exit 1
fi
cp "$RPM_FILE" "$BUILD_DIR/"
echo "Built: $BUILD_DIR/$(basename "$RPM_FILE")"
