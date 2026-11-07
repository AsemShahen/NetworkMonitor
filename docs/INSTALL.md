# Install Network Monitor

Network Monitor runs on Linux with cgroup v2 and glibc 2.34 or newer. The
release packages bundle Python, Qt/PySide6, pyqtgraph, numpy, and pyroute2. The
privileged helper uses the system `python3`.

## Requirements

- A modern Debian/Ubuntu or Fedora/RHEL system with cgroup v2.
- `pyroute2` for native Netlink counters. It is bundled in the release
  packages; source installs need `python3 -m pip install pyroute2`.
- `iproute2` (`ss`) is an optional fallback and is recommended.
- `nftables` and `polkit` (`pkexec`) for blocking.
- A Wayland or X11 desktop.

Without Netlink or `ss`, Network Monitor still discovers connections from
`/proc/net` but cannot show byte counters. UDP/QUIC sockets are always shown as
“speed unavailable” because the kernel does not expose reliable byte counters
for them.

Install the host tools:

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install -y iproute2 nftables polkitd pkexec libxcb-cursor0

# Fedora / RHEL
sudo dnf install -y iproute nftables polkit libxcb
```

## Option 1: signed APT repository (Debian / Ubuntu)

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
echo "deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] https://asemshahen.github.io/NetworkMonitor/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/network-monitor.list
sudo apt update
sudo apt install network-monitor
```

## Option 2: signed RPM repository (Fedora / RHEL)

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/rpm/network-monitor.repo \
  -o /etc/yum.repos.d/network-monitor.repo
sudo dnf install network-monitor
```

The RPM repository uses `repo_gpgcheck=1`, so DNF verifies the signed
`repomd.xml` before installing.

## Option 3: direct release packages

Download from <https://github.com/AsemShahen/NetworkMonitor/releases>:

- `network-monitor_<version>_amd64.deb`
- `network-monitor-<version>-1.x86_64.rpm`
- `NetworkMonitor-<version>-x86_64.AppImage`
- `NetworkMonitor-<version>-linux-x86_64.tar.gz` (manual `/opt` updates)
- `SHA256SUMS`
- `SHA256SUMS.asc`

Verify the download:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

Install the package:

```bash
sudo apt install ./network-monitor_<version>_amd64.deb
# or
sudo dnf install ./network-monitor-<version>-1.x86_64.rpm
```

## Option 4: AppImage

```bash
chmod +x NetworkMonitor-<version>-x86_64.AppImage
./NetworkMonitor-<version>-x86_64.AppImage
```

The AppImage bundles the application and helper. Blocking still requires host
`pkexec`, `python3`, `nftables`, and cgroup v2.

## Updates

Version 1.0.6 and later have **Settings → Application updates → Check for
updates**. The updater supports manual `/opt/network-monitor` installs,
AppImage, `.deb`, `.rpm`, and Flatpak. It verifies `SHA256SUMS` and
`SHA256SUMS.asc` before installing and uses `pkexec` for system installs.

For a manual `/opt` install from 1.0.5 or older, install 1.0.8 once:

```bash
tar -xzf NetworkMonitor-1.0.8-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

After that, later releases can be installed with the update button. The
updater keeps a timestamped backup in `/opt` and restores it automatically if
the manual installation fails.

## Background collection (optional)

Version 1.0.7 adds **Settings → Background collection → Collect monthly usage
while Network Monitor is closed**. It installs and enables a systemd user
service in `~/.config/systemd/user/network-monitor-collector.service`; no root
access is needed.

The service uses the same
`~/.local/share/network-monitor/usage.db` as the application. A single-writer
`flock` on `usage.db.lock` prevents the GUI and collector from writing usage at
the same time. The application hands the writer role to the collector when the
service starts and takes it back when the service is disabled.

Status is written to `~/.local/share/network-monitor/collector.json`. Enable or
disable collection from the same Settings checkbox; disabling it returns usage
counting to the GUI only while the application is open.

The feature requires a working systemd user session. If systemd is unavailable,
the setting is disabled and the application continues counting while it is
open.

## Option 5: Arch Linux (AUR)

The AUR package name is `network-monitor-qt-bin` (submission pending). It
unpacks the official `.deb` release and installs the application, helper,
polkit policy, icons, and desktop file.

```bash
# once the package is accepted in AUR
yay -S network-monitor-qt-bin
# or
paru -S network-monitor-qt-bin
```

> The existing AUR package `network-monitor-bin` belongs to a different
> project. Use `network-monitor-qt-bin` for this application.

## Option 6: install from source

```bash
git clone https://github.com/AsemShahen/NetworkMonitor.git
cd NetworkMonitor
./install.sh
network-monitor
```

The script installs to `/opt/network-monitor`, adds a launcher in
`/usr/local/bin/network-monitor`, installs the helper and polkit policy, and
adds desktop icons. If `build/runtime` exists, `install.sh` copies it into
`/opt/network-monitor/runtime`; otherwise the app uses the system Python.

To get the same bundled runtime as the packages (including `pyroute2`), run:

```bash
./packaging/build-runtime.sh
./install.sh
```

When no bundled runtime is available, install the interface dependencies in
the system Python environment:

```bash
python3 -m pip install --user PySide6 pyqtgraph numpy pyroute2
```

Packaged releases do not need this step because the runtime is bundled.

## Verify the installation

Open **Settings → Diagnostics**. A working setup shows:

```text
Engine: netlink — ready
Netlink: available
Sockets: … (TCP …, UDP …)
```

If Netlink is unavailable, install `pyroute2` or keep `iproute2` installed so
the `ss` fallback can provide counters. The final `/proc/net` mode lists
connections but reports that byte counters are unavailable.

Monthly and daily usage is stored in
`~/.local/share/network-monitor/usage.db`. It is counted while Network Monitor
is running, or continuously when the optional background collector is enabled
in Settings.

## Verify the signing key

The repository is signed by:

```text
Network Monitor packages <asemshahen5@gmail.com>
Fingerprint: D53CB321C38875CCA82128CC77EED1C545319AE8
```

> If you added the repository before 2026-10-28, re-import the public key with
> the commands above. The repository was republished with a new signing key
> after the previous key was lost.

Check the key after importing it:

```bash
gpg --show-keys /etc/apt/keyrings/network-monitor.gpg
# or
rpm --import https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc
rpm -qa gpg-pubkey --qf '%{SUMMARY} %{VERSION}\n' | grep -i 'Network Monitor'
```

## Uninstall

```bash
# Debian / Ubuntu
sudo apt remove network-monitor

# Fedora / RHEL
sudo dnf remove network-monitor

# Source install
sudo ./uninstall.sh
```

User settings and the blocklist remain in `~/.config/network-monitor/` and
`~/.local/share/network-monitor/`.
