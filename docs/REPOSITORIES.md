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

## Current repository packages (v1.0.1)

The repository serves the official `v1.0.1` release assets, so these hashes
match `SHA256SUMS` and the AUR source.

The `v1.0.2` and `v1.0.3` releases are available on GitHub Releases, but the
repository remains on `v1.0.1` until the existing signing key is restored. Do not replace
the key blindly: clients already trust the fingerprint below, and a new key
would make `apt update` and `dnf` fail until every client imports it.

- `.deb`: `90,981,106` bytes, SHA-256
  `b36e747f21c7eb8db1e9cba49341aad001c68326d2016043c6412f20f16ef161`
- `.rpm`: `91,608,523` bytes, SHA-256
  `5d1c165d2330f760c2089496b21402c95978dbad52bcbd158c0534a49b5c1700`
- GPG fingerprint:
  `4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`

The AUR package uses the same official release `.deb`.

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

Future releases publish automatically from `.github/workflows/release.yml` when
`GPG_PRIVATE_KEY` is configured. If the secret is missing, the release still
succeeds and the repository step is skipped with a warning.

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
