# AUR package: `network-monitor-qt-bin`

This directory contains the Arch Linux binary package for Network Monitor. It
downloads the official `.deb` release asset, verifies its SHA-256, and installs
the application, privileged helper, polkit policy, icons, and desktop file.

## Name

The AUR name `network-monitor-bin` already belongs to a different project
(Rust/GTK4). This package is therefore named `network-monitor-qt-bin` to avoid
a collision. It provides and conflicts with `network-monitor`; it also conflicts
with `network-monitor-bin` because both install a `network-monitor` executable.

## Build locally

```bash
cd packaging/aur
makepkg -si
```

The current `PKGBUILD` uses:

- Version: `1.0.3`
- Source: `https://github.com/AsemShahen/NetworkMonitor/releases/download/v1.0.3/network-monitor_1.0.3_amd64.deb`
- SHA-256: `603170ecc2f67d9fa942294da04232d6eedb266b28edac43648c712539cd4991`

## Submit to AUR

1. Create an AUR account at <https://aur.archlinux.org/>.
2. Add your SSH public key in **My Account → SSH Public Key**.
3. Clone the empty package repository:

   ```bash
   git clone ssh://aur@aur.archlinux.org/network-monitor-qt-bin.git
   cd network-monitor-qt-bin
   ```

4. Copy `PKGBUILD`, `.SRCINFO`, and `network-monitor-qt-bin.install` from this
   directory.
5. Commit and push:

   ```bash
   git add PKGBUILD .SRCINFO network-monitor-qt-bin.install
   git commit -m "Initial import: network-monitor-qt-bin 1.0.3"
   git push
   ```

6. Verify the package page:
   <https://aur.archlinux.org/packages/network-monitor-qt-bin>

## Update for a new release

1. Update `pkgver` and `sha256sums` in `PKGBUILD`.
2. Regenerate metadata:

   ```bash
   makepkg --printsrcinfo > .SRCINFO
   ```

3. Commit and push both files.

The source must remain the official release `.deb`; do not point it at a local
build. That keeps the AUR checksum reproducible for every user.
