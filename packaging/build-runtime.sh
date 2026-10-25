#!/usr/bin/env bash
# Build the self-contained Python/PySide6 runtime used by the .deb, .rpm and AppImage packages.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
RUNTIME="$BUILD_DIR/runtime"

PYTHON_VERSION="${PYTHON_VERSION:-3.12.15}"
PYTHON_RELEASE="${PYTHON_RELEASE:-20261021}"
PYSIDE_VERSION="${PYSIDE_VERSION:-6.12.0}"
PYQTGRAPH_VERSION="${PYQTGRAPH_VERSION:-0.14.0}"
NUMPY_VERSION="${NUMPY_VERSION:-2.5.4}"

PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PYTHON_RELEASE}/cpython-${PYTHON_VERSION}%2B${PYTHON_RELEASE}-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz"
ARCHIVE="$BUILD_DIR/python-runtime.tar.gz"

mkdir -p "$BUILD_DIR"

command -v curl >/dev/null 2>&1 || { echo "curl is required" >&2; exit 1; }
command -v tar >/dev/null 2>&1 || { echo "tar is required" >&2; exit 1; }

if [ ! -x "$RUNTIME/bin/python3" ]; then
    echo "Downloading Python ${PYTHON_VERSION} (${PYTHON_RELEASE})..."
    curl -fL --retry 3 "$PYTHON_URL" -o "$ARCHIVE"
    rm -rf "$RUNTIME"
    mkdir -p "$RUNTIME"
    tar -xzf "$ARCHIVE" -C "$RUNTIME" --strip-components=1
    rm -f "$ARCHIVE"
fi

if ! "$RUNTIME/bin/python3" -c "import PySide6, pyqtgraph, numpy" >/dev/null 2>&1; then
    if ! "$RUNTIME/bin/python3" -m pip --version >/dev/null 2>&1; then
        "$RUNTIME/bin/python3" -m ensurepip --upgrade >/dev/null
    fi
    echo "Installing PySide6 ${PYSIDE_VERSION}, pyqtgraph ${PYQTGRAPH_VERSION}, numpy ${NUMPY_VERSION}..."
    "$RUNTIME/bin/python3" -m pip install \
        --no-cache-dir \
        --disable-pip-version-check \
        --no-warn-script-location \
        "PySide6-Essentials==${PYSIDE_VERSION}" \
        "pyqtgraph==${PYQTGRAPH_VERSION}" \
        "numpy==${NUMPY_VERSION}"
fi

# Remove build-only and unused runtime files to keep the packages reasonable.
PY_LIB="$RUNTIME/lib/python${PYTHON_VERSION%.*}"
rm -rf \
    "$PY_LIB/test" \
    "$PY_LIB/idlelib" \
    "$PY_LIB/tkinter" \
    "$PY_LIB/turtledemo" \
    "$PY_LIB/site-packages/pip" \
    "$PY_LIB/site-packages/pip-"* \
    "$PY_LIB/site-packages/setuptools" \
    "$PY_LIB/site-packages/setuptools-"* \
    "$PY_LIB/site-packages/pkg_resources" \
    "$PY_LIB/site-packages/wheel" \
    "$PY_LIB/site-packages/wheel-"* \
    "$RUNTIME/include" \
    "$RUNTIME/share/man" \
    "$RUNTIME/share/doc" \
    "$RUNTIME/lib/python${PYTHON_VERSION%.*}/site-packages/PySide6/Qt/qml" \
    "$RUNTIME/lib/python${PYTHON_VERSION%.*}/site-packages/PySide6/Qt/translations" \
    "$RUNTIME/lib/python${PYTHON_VERSION%.*}/site-packages/PySide6/Qt/lib/cmake" \
    "$RUNTIME/lib/python${PYTHON_VERSION%.*}/site-packages/PySide6/Qt/plugins/sqldrivers" \
    "$RUNTIME/lib/python${PYTHON_VERSION%.*}/site-packages/PySide6/include" \
    "$RUNTIME/lib/python${PYTHON_VERSION%.*}/site-packages/PySide6/typesystems"

find "$RUNTIME" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$RUNTIME" -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

echo "Runtime ready: $RUNTIME"
du -sh "$RUNTIME"
