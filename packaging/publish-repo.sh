#!/usr/bin/env bash
# Build a signed APT/RPM package repository and optionally publish it to gh-pages.
# The gh-pages tree is replaced on each publish; older versions remain on
# GitHub Releases.
#
# Required for signing:
#   GPG_PRIVATE_KEY       armored private key (GitHub Actions secret)
#   or GPG_PRIVATE_KEY_FILE
#   GPG_PASSPHRASE        optional key passphrase
#   GPG_KEY_ID            optional; derived from the imported key
#
# Required for publishing (PUBLISH=1):
#   GITHUB_TOKEN
#   GITHUB_REPOSITORY     owner/repo
#
# Local build only:
#   PUBLISH=0 ./packaging/publish-repo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
REPO_DIR="${REPO_DIR:-$BUILD_DIR/repo}"
PAGES_BRANCH="${PAGES_BRANCH:-gh-pages}"
PUBLISH="${PUBLISH:-0}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-AsemShahen/NetworkMonitor}"
REPO_OWNER="${GITHUB_REPOSITORY%%/*}"
REPO_NAME="${GITHUB_REPOSITORY#*/}"
PAGES_BASE_URL="${PAGES_BASE_URL:-https://${REPO_OWNER,,}.github.io/${REPO_NAME}}"
PAGES_BASE_URL="${PAGES_BASE_URL%/}"
VERSION="${VERSION:-$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT/src/netmon/__init__.py")}"

need() {
    command -v "$1" >/dev/null 2>&1 || {
        echo "error: $1 is required" >&2
        exit 1
    }
}

need gpg
need gzip
need apt-ftparchive

if command -v createrepo_c >/dev/null 2>&1; then
    CREATEREPO=(createrepo_c)
elif command -v createrepo >/dev/null 2>&1; then
    CREATEREPO=(createrepo)
else
    echo "error: createrepo_c or createrepo is required" >&2
    exit 1
fi

shopt -s nullglob
DEBS=("$BUILD_DIR"/network-monitor_*.deb)
RPMS=("$BUILD_DIR"/network-monitor-*.rpm)
shopt -u nullglob

if [ "${#DEBS[@]}" -eq 0 ]; then
    echo "error: no .deb files found in $BUILD_DIR" >&2
    exit 1
fi
if [ "${#RPMS[@]}" -eq 0 ]; then
    echo "error: no .rpm files found in $BUILD_DIR" >&2
    exit 1
fi

# GitHub rejects files larger than 100 MiB in a git repository. GitHub Pages
# serves from a branch, so fail early instead of failing halfway through a push.
MAX_PACKAGE_SIZE="${MAX_PACKAGE_SIZE:-104857600}"
if [ "$PUBLISH" = "1" ]; then
    for f in "${DEBS[@]}" "${RPMS[@]}"; do
        size="$(stat -c %s "$f")"
        if [ "$size" -gt "$MAX_PACKAGE_SIZE" ]; then
            echo "error: $(basename "$f") is $size bytes, larger than GitHub's ${MAX_PACKAGE_SIZE}-byte limit." >&2
            echo "       Rebuild with zstd compression (see %_binary_payload in packaging/network-monitor.spec) or publish a new release." >&2
            exit 1
        fi
    done
fi

# Import the signing key into a private keyring unless the caller provided one.
if [ -z "${GNUPGHOME:-}" ]; then
    GNUPGHOME="$(mktemp -d)"
    export GNUPGHOME
    trap 'rm -rf "$GNUPGHOME"' EXIT
fi

if [ -n "${GPG_PRIVATE_KEY_FILE:-}" ]; then
    gpg --batch --import "$GPG_PRIVATE_KEY_FILE"
elif [ -n "${GPG_PRIVATE_KEY:-}" ]; then
    # GitHub secrets sometimes store an armored key as one line with literal
    # "\n" sequences (or as a JSON-quoted string). Normalize those forms before
    # importing, without ever printing the key.
    KEY_FILE="$(mktemp)"
    chmod 600 "$KEY_FILE"
    GPG_PRIVATE_KEY="$GPG_PRIVATE_KEY" python3 - "$KEY_FILE" <<'PY'
import json
import os
import sys

value = os.environ.get("GPG_PRIVATE_KEY", "")
if value.startswith('"') and value.endswith('"'):
    try:
        value = json.loads(value)
    except ValueError:
        pass
value = value.replace("\\r\\n", "\n").replace("\\n", "\n")
if not value.endswith("\n"):
    value += "\n"
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    handle.write(value)
PY
    gpg --batch --import "$KEY_FILE"
    rm -f "$KEY_FILE"
fi

GPG_KEY_ID="${GPG_KEY_ID:-$(gpg --batch --list-secret-keys --with-colons 2>/dev/null | awk -F: '/^fpr:/ {print $10; exit}')}"
if [ -z "$GPG_KEY_ID" ]; then
    echo "error: no GPG secret key available; set GPG_PRIVATE_KEY or GPG_PRIVATE_KEY_FILE" >&2
    exit 1
fi

gpg_sign() {
    gpg --batch --yes --pinentry-mode loopback \
        --passphrase "${GPG_PASSPHRASE:-}" \
        --local-user "$GPG_KEY_ID" "$@"
}

if [ "$PUBLISH" = "1" ]; then
    need git
    if [ -z "${REPO_URL:-}" ]; then
        : "${GITHUB_TOKEN:?GITHUB_TOKEN is required when PUBLISH=1}"
        REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
    fi

    # Publish a fresh tree with only the current packages. Older versions stay
    # on GitHub Releases, which keeps the Pages site and git history small.
    rm -rf "$REPO_DIR"
    mkdir -p "$REPO_DIR"
    git -C "$REPO_DIR" init -q
    git -C "$REPO_DIR" checkout -q --orphan "$PAGES_BRANCH"
else
    rm -rf "$REPO_DIR"
    mkdir -p "$REPO_DIR"
fi

APT_DIR="$REPO_DIR/apt"
APT_POOL="$APT_DIR/pool/main/n/network-monitor"
APT_DIST="$APT_DIR/dists/stable"
APT_BIN="$APT_DIST/main/binary-amd64"
RPM_DIR="$REPO_DIR/rpm/x86_64"
mkdir -p "$APT_POOL" "$APT_BIN" "$RPM_DIR" "$REPO_DIR/keys"
: > "$REPO_DIR/.nojekyll"

cp -f "${DEBS[@]}" "$APT_POOL/"
cp -f "${RPMS[@]}" "$RPM_DIR/"

# APT repository metadata. The Release file is signed, so APT verifies the
# Packages checksums before downloading a package.
(
    cd "$APT_DIR"
    apt-ftparchive packages pool > "$APT_BIN/Packages"
    gzip -9 -n -c "$APT_BIN/Packages" > "$APT_BIN/Packages.gz"
    rm -f "$APT_DIST/Release" "$APT_DIST/InRelease" "$APT_DIST/Release.gpg"
    apt-ftparchive \
        -o APT::FTPArchive::Release::Origin="Network Monitor" \
        -o APT::FTPArchive::Release::Label="Network Monitor" \
        -o APT::FTPArchive::Release::Suite="stable" \
        -o APT::FTPArchive::Release::Codename="stable" \
        -o APT::FTPArchive::Release::Architectures="amd64" \
        -o APT::FTPArchive::Release::Components="main" \
        -o APT::FTPArchive::Release::Description="Network Monitor packages" \
        release dists/stable > "$APT_DIR/Release.tmp"
    mv "$APT_DIR/Release.tmp" "$APT_DIST/Release"
    gpg_sign --clearsign -o "$APT_DIST/InRelease" "$APT_DIST/Release"
    gpg_sign --detach-sign --armor -o "$APT_DIST/Release.gpg" "$APT_DIST/Release"
)

# RPM repository metadata. The metadata is signed; packages are protected by
# the checksums inside the signed repomd.xml.
"${CREATEREPO[@]}" --update "$RPM_DIR"
gpg_sign --detach-sign --armor -o "$RPM_DIR/repodata/repomd.xml.asc" "$RPM_DIR/repodata/repomd.xml"

gpg --armor --export "$GPG_KEY_ID" > "$REPO_DIR/keys/network-monitor.asc"
gpg --with-colons --fingerprint "$GPG_KEY_ID" | awk -F: '/^fpr:/ {print $10; exit}' > "$REPO_DIR/keys/fingerprint.txt"

cat > "$REPO_DIR/rpm/network-monitor.repo" <<EOF
[network-monitor]
name=Network Monitor
baseurl=${PAGES_BASE_URL}/rpm/x86_64
enabled=1
# Package integrity is covered by the signed repomd.xml metadata.
gpgcheck=0
repo_gpgcheck=1
gpgkey=${PAGES_BASE_URL}/keys/network-monitor.asc
metadata_expire=6h
EOF

cat > "$REPO_DIR/apt/network-monitor.list" <<EOF
deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] ${PAGES_BASE_URL}/apt stable main
EOF

cat > "$REPO_DIR/index.html" <<EOF
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Network Monitor packages</title>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: system-ui, sans-serif; line-height: 1.6; max-width: 58rem; margin: 2rem auto; padding: 0 1rem; }
    pre { overflow-x: auto; padding: 1rem; background: #f4f4f4; border-radius: .4rem; }
    code { font-family: ui-monospace, monospace; }
    @media (prefers-color-scheme: dark) { pre { background: #222; } }
  </style>
</head>
<body>
  <h1>Network Monitor packages</h1>
  <p>Signed package repository for <a href="https://github.com/${GITHUB_REPOSITORY}">Network Monitor</a>.</p>
  <p>GPG fingerprint: <code>$(cat "$REPO_DIR/keys/fingerprint.txt")</code></p>

  <h2>Debian / Ubuntu</h2>
  <pre><code>sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL ${PAGES_BASE_URL}/keys/network-monitor.asc | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
echo "deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] ${PAGES_BASE_URL}/apt stable main" | sudo tee /etc/apt/sources.list.d/network-monitor.list
sudo apt update
sudo apt install network-monitor</code></pre>

  <h2>Fedora / RHEL</h2>
  <pre><code>sudo curl -fsSL ${PAGES_BASE_URL}/rpm/network-monitor.repo -o /etc/yum.repos.d/network-monitor.repo
sudo dnf install network-monitor</code></pre>

  <p><a href="https://github.com/${GITHUB_REPOSITORY}/releases">GitHub Releases</a></p>
</body>
</html>
EOF

if [ "$PUBLISH" = "1" ]; then
    cd "$REPO_DIR"
    git config user.name "github-actions[bot]"
    git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
    git add -A
    if git diff --cached --quiet; then
        echo "No repository changes to publish."
    else
        git commit -m "Update package repository for ${VERSION}"
        git push --force "$REPO_URL" "HEAD:${PAGES_BRANCH}"
        echo "Published: ${PAGES_BASE_URL}/"
    fi
    rm -rf "$REPO_DIR/.git"
else
    echo "Repository built at: $REPO_DIR"
fi
