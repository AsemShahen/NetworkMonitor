# Signed package repositories

Network Monitor can be installed from a signed APT repository (Debian/Ubuntu)
and a signed RPM repository (Fedora/RHEL). The repository is published to the
`gh-pages` branch and served by GitHub Pages:

<https://asemshahen.github.io/NetworkMonitor/>

The repository contains:

- `apt/` — APT metadata, `InRelease`, `Release.gpg`, and the `.deb` pool.
- `rpm/` — RPM metadata, signed `repomd.xml`, and the `.rpm` files.
- `keys/network-monitor.asc` — public signing key.
- `keys/fingerprint.txt` — key fingerprint.

`packaging/publish-repo.sh` builds the repository from the packages in
`build/`, signs the metadata, and (when `PUBLISH=1`) pushes the result to
`gh-pages`. It publishes a fresh tree containing only the current packages;
older versions remain available on GitHub Releases. This keeps the Pages site
and git history small.

## Current repository packages (v1.1.0)

The repository currently serves the official `v1.1.0` release assets, so these
hashes match `SHA256SUMS` and the AUR source.

The `v1.0.2` through `v1.0.9` releases remain available on GitHub Releases. The
repository now serves `v1.1.0`, signed with the current key. Existing clients
trust the previous fingerprint below and must import the new public key before
the next `apt update` or `dnf` refresh.

- `.deb`: `92,341,976` bytes, SHA-256
  `02749e5dbe4e026ff45776deb771410c0255a7d98cb94efcc2e3dab1303f6a4a`
- `.rpm`: `93,079,874` bytes, SHA-256
  `9307bbb01f4009a352ff2e5ed9bcb3fc848862ef3079c169ed6878c370f4952c`
- Manual update archive: `125,051,321` bytes, SHA-256
  `a79b823d6381845a286fa075171dd26694faca6fa78ddee9e823957827d3ce63`
- AppImage: `112,024,056` bytes, SHA-256
  `5ca74cd95e8c520fb504835fcdd4c89255e7311fbb8037863f8a090ccf8898ec`
- AppImage zsync: `191,694` bytes, SHA-256
  `ccd29e39c4b98f43a03327c9b821144b8761878eb111c12c099b3a7f166dceee`
- Previous fingerprint (clients installed before 2026-10-28):
  `4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`
- Current fingerprint:
  `D53CB321C38875CCA82128CC77EED1C545319AE8`

### Migrate existing APT/RPM clients

After the repository is republished, existing clients must import the new
public key once.

APT:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
sudo apt update
```

RPM:

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  -o /etc/pki/rpm-gpg/RPM-GPG-KEY-network-monitor
sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-network-monitor
sudo dnf clean all
sudo dnf makecache
```

The AUR package uses the official `v1.1.0` release `.deb`.

## One-time setup

### 1. Create a signing key

Run this on a trusted machine, not in CI:

```bash
gpg --full-generate-key
```

Recommended: RSA 4096, expiry 2 years, a clear name such as
`Network Monitor packages`, and the project email.

Find the fingerprint and export the keys:

```bash
KEY_ID=$(gpg --list-secret-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')
echo "$KEY_ID"
gpg --armor --export-secret-keys "$KEY_ID" > network-monitor-private.asc
gpg --armor --export "$KEY_ID" > network-monitor-public.asc
```

Keep `network-monitor-private.asc` offline. Delete it after adding the GitHub
secret.

### 2. Add GitHub Actions secrets

In the repository: **Settings → Secrets and variables → Actions → New repository secret**.

- `GPG_PRIVATE_KEY` — the full contents of `network-monitor-private.asc`.
- `GPG_PASSPHRASE` — the key passphrase, if the key has one. Omit it for an
  unprotected key.
- `GPG_KEY_ID` — optional. The workflow derives the fingerprint automatically.

Never commit the private key or the passphrase.

### 3. Publish the first repository

Run **Actions → Publish package repository → Run workflow** with the tag of an
existing release built after the zstd change, for example `v1.0.1`.

The workflow downloads the release `.deb` and `.rpm`, builds the metadata,
signs it, creates the `gh-pages` branch if needed, and pushes it.

GitHub rejects files larger than 100 MiB in a git repository. The RPM spec now
uses zstd level 19 to keep the bundled runtime under that limit. If you publish
an older release whose RPM was built with gzip (such as `v1.0.0`), create a new
release from the current source and publish that tag instead. GitHub Releases
can still host the larger old asset.

### 4. Enable GitHub Pages

After the first successful run, open **Settings → Pages** and set:

- **Source:** Deploy from a branch
- **Branch:** `gh-pages`
- **Folder:** `/ (root)`

Save. GitHub Pages will publish the repository at:

<https://asemshahen.github.io/NetworkMonitor/>

Automatic repository publication from `.github/workflows/release.yml` is
gated by the repository variable `PUBLISH_SIGNED_REPOSITORY=true`. The new key
was generated on 2026-10-28; its private key and passphrase are stored locally
and are not committed. The repository was republished with `v1.1.0` on
2026-11-09, and both `InRelease` and `repomd.xml.asc` verify against the new
fingerprint.

The previous key (`4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`) is
unrecoverable. The new key replaces it; existing clients must run the migration
commands above.

## Install from the repository

### Debian / Ubuntu

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
echo "deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] https://asemshahen.github.io/NetworkMonitor/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/network-monitor.list
sudo apt update
sudo apt install network-monitor
```

### Fedora / RHEL

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/rpm/network-monitor.repo \
  -o /etc/yum.repos.d/network-monitor.repo
sudo dnf install network-monitor
```

The RPM repository uses `repo_gpgcheck=1`: DNF verifies the signed
`repomd.xml` and the package checksums it contains. Package-level RPM
signatures are not enabled yet (`gpgcheck=0`).

## Verify the signatures manually

```bash
base=https://asemshahen.github.io/NetworkMonitor
curl -fsSL "$base/keys/network-monitor.asc" | gpg --import
curl -fsSL "$base/apt/dists/stable/InRelease" -o /tmp/InRelease
gpg --verify /tmp/InRelease
curl -fsSL "$base/rpm/x86_64/repodata/repomd.xml" -o /tmp/repomd.xml
curl -fsSL "$base/rpm/x86_64/repodata/repomd.xml.asc" -o /tmp/repomd.xml.asc
gpg --verify /tmp/repomd.xml.asc /tmp/repomd.xml
```

Compare the fingerprint with `keys/fingerprint.txt` and with the key you
created.

## Local repository build

To build and sign a repository without pushing it:

```bash
PUBLISH=0 ./packaging/publish-repo.sh
```

The output is written to `build/repo/`. You need `apt-ftparchive`, `createrepo_c`
(or `createrepo`), `gpg`, and a signing key in your keyring.

## AUR and AppImageHub

- Arch Linux: see [`packaging/aur/README_AR.md`](../packaging/aur/README_AR.md).
  The AUR package name is `network-monitor-qt-bin` (the existing
  `network-monitor-bin` belongs to a different project).
- AppImageHub: see [`packaging/appimagehub/README.md`](../packaging/appimagehub/README.md)
  or the Arabic [`README_AR.md`](../packaging/appimagehub/README_AR.md).

## Troubleshooting

- **Pages returns 404:** confirm the `gh-pages` branch exists and Pages is set
  to that branch.
- **`gh-pages` push rejected:** remove branch protection from `gh-pages`; it is
  a generated branch that is replaced on every publish.
- **`createrepo_c: command not found`:** install `createrepo-c` (Ubuntu/Debian)
  or `createrepo_c` (Fedora).
- **`GPG_PRIVATE_KEY is not configured`:** add the repository secret, then rerun
  the workflow.
- **`is larger than GitHub's ... limit`:** the package was built without zstd;
  create a new release from the current source and publish that tag.
- **APT says `NO_PUBKEY`:** reinstall the key with the command above; do not use
  `[trusted=yes]`.
- **DNF says `repomd.xml` signature verification failed:** confirm the
  `gpgkey` URL is reachable and the `repomd.xml.asc` file exists.
