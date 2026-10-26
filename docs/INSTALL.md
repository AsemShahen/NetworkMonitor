# Install Network Monitor

Network Monitor runs on Linux with cgroup v2 and glibc 2.34 or newer. The
release packages bundle Python, Qt/PySide6, pyqtgraph, and numpy. The privileged
helper uses the system `python3`.

## Requirements

- A modern Debian/Ubuntu or Fedora/RHEL system with cgroup v2.
- `iproute2` (`ss`) for accurate per-process counters.
- `nftables` and `polkit` (`pkexec`) for blocking.
- A Wayland or X11 desktop.

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
- `SHA256SUMS`

Verify the download:

```bash
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
adds desktop icons.

## Verify the signing key

The repository is signed by:

```text
Network Monitor packages <asemshahen5@gmail.com>
Fingerprint: 4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE
```

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
