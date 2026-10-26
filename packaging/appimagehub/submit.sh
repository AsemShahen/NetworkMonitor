#!/usr/bin/env bash
# Prepare an AppImageHub pull request from an existing fork.
# The fork must already exist under $GITHUB_USER (or the first argument).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OWNER="${1:-${GITHUB_USER:-}}"
WORK="${WORKDIR:-/tmp/opencode/appimagehub-submit}"
BRANCH="${BRANCH:-add-network-monitor}"

if [ -z "$OWNER" ]; then
    echo "usage: GITHUB_USER=your-user $0 [fork-owner]" >&2
    exit 1
fi

FORK_URL="https://github.com/${OWNER}/appimage.github.io.git"
echo "Using fork: ${FORK_URL}"

if ! git ls-remote "$FORK_URL" HEAD >/dev/null 2>&1; then
    echo "error: fork not found. Fork https://github.com/AppImage/appimage.github.io first." >&2
    exit 1
fi

rm -rf "$WORK"
git clone --depth 1 "$FORK_URL" "$WORK"
cd "$WORK"

if [ -e data/Network_Monitor ]; then
    echo "error: data/Network_Monitor already exists in the fork." >&2
    exit 1
fi

cp "$ROOT/packaging/appimagehub/Network_Monitor" data/Network_Monitor
git checkout -b "$BRANCH"
git add data/Network_Monitor
git commit -m "Add Network_Monitor"
git push -u origin "$BRANCH"

cat <<EOF
Pushed branch ${BRANCH}.

Open the pull request here:
https://github.com/AppImage/appimage.github.io/compare/master...${OWNER}:${BRANCH}?expand=1

Keep the pull request limited to data/Network_Monitor.
EOF
