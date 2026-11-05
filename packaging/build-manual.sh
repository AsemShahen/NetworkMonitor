#!/usr/bin/env bash
# Build the signed-manual-update archive used by the in-app updater.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
VERSION="${VERSION:-$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/src/netmon/__init__.py")}"
RUNTIME="$BUILD_DIR/runtime"
OUT="$BUILD_DIR/NetworkMonitor-${VERSION}-linux-x86_64.tar.gz"
STAGE="$BUILD_DIR/manual-stage.$$"
rm -rf "$STAGE"

cleanup() {
    rm -rf "$STAGE"
}
trap cleanup EXIT

if [ ! -x "$RUNTIME/bin/python3" ]; then
    "$ROOT/packaging/build-runtime.sh"
fi

mkdir -p "$STAGE/network-monitor"
cp -a "$RUNTIME" "$STAGE/network-monitor/runtime"
cp -a "$ROOT/src" "$STAGE/network-monitor/src"
cp -a "$ROOT/bin" "$ROOT/data" "$ROOT/docs" "$ROOT/packaging" "$ROOT/tests" \
    "$STAGE/network-monitor/"
install -m 755 "$ROOT/network-monitor" "$STAGE/network-monitor/network-monitor"
install -m 644 "$ROOT/REPORT_AR.md" "$ROOT/pyproject.toml" "$STAGE/network-monitor/"
install -m 644 "$ROOT/LICENSE" "$STAGE/network-monitor/LICENSE"
install -m 644 "$ROOT/README.md" "$STAGE/network-monitor/README.md"
install -m 644 "$ROOT/README_AR.md" "$STAGE/network-monitor/README_AR.md"
install -m 755 "$ROOT/install.sh" "$STAGE/network-monitor/install.sh"
install -m 755 "$ROOT/uninstall.sh" "$STAGE/network-monitor/uninstall.sh"

find "$STAGE/network-monitor" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$STAGE/network-monitor" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

rm -f "$OUT"
tar -C "$STAGE" -czf "$OUT" network-monitor
test -s "$OUT"
LISTING="$(tar -tzf "$OUT")"
if ! grep -qx 'network-monitor/network-monitor' <<<"$LISTING"; then
    echo "error: manual archive is missing network-monitor/network-monitor" >&2
    exit 1
fi
if ! grep -qx 'network-monitor/runtime/bin/python3' <<<"$LISTING"; then
    echo "error: manual archive is missing the bundled runtime" >&2
    exit 1
fi
echo "Built: $OUT"
ls -lh "$OUT"
