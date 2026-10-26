# Network Monitor

A dark, bilingual (English/Arabic) desktop network monitor for Linux (Debian/Ubuntu and Fedora) that shows per-application download/upload speed and lets you block any application with cgroup v2 + nftables.

## Features
- Live per-process download and upload rates (KB/s–MB/s).
- Active connections, full executable paths, CPU and RSS.
- Session totals plus top summary cards.
- Interactive time-series chart.
- Search, sortable columns, hide-idle filter.
- Export visible application names to a text file.
- Real block/unblock via cgroup v2 + nftables with polkit authentication.
- Persistent blocklist with import/export and apply-on-start.
- English and Arabic interfaces with instant switching in Settings (English is the default), RTL support, dark theme, tray icon, and desktop integration.

## Download
Prebuilt packages are published on **GitHub Releases**:

<https://github.com/AsemShahen/NetworkMonitor/releases>

- **Debian/Ubuntu:** `network-monitor_<version>_amd64.deb`
- **Fedora/RHEL:** `network-monitor-<version>-1.x86_64.rpm`
- **Portable:** `NetworkMonitor-<version>-x86_64.AppImage`

The `.deb` and `.rpm` packages install the privileged helper and the polkit policy. The AppImage contains the helper, but blocking still requires host `pkexec`, `python3`, `nftables`, and cgroup v2.

## Install from the signed package repository

Once the repository is published, you can install and update Network Monitor with your package manager. The repository is signed with GPG; the public key and fingerprint are published at <https://asemshahen.github.io/NetworkMonitor/>.

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

If the repository is not available yet, use the GitHub Releases packages above. Maintainers can find the repository setup in [docs/REPOSITORIES.md](docs/REPOSITORIES.md).

## Quick start
```bash
./network-monitor
```

## Install system-wide
```bash
./install.sh
network-monitor
```
See `docs/INSTALL_AR.md` and `docs/FIRST_RUN_AR.md` (Arabic).

## Build packages
The release workflow builds all three formats on every `v*` tag. To build locally:

```bash
./packaging/build-runtime.sh
./packaging/build-deb.sh
./packaging/build-rpm.sh
./packaging/build-appimage.sh
```

Output is written to `build/`. See `packaging/README_AR.md` for details and required tools.

## Requirements
- Linux with cgroup v2 and glibc 2.34 or newer (the bundled Qt/PySide6 runtime requires it).
- `iproute2` (`ss`) for accurate per-process counters.
- `nftables` + `polkit` (`pkexec`) for blocking.
- The app runtime (Python, PySide6, pyqtgraph, numpy) is bundled in the release packages; the privileged helper uses the system `python3`.

## Tests
```bash
./packaging/build-runtime.sh
PYTHONPATH=src build/runtime/bin/python3 -m unittest discover -s tests -v
```

## Author
**Author:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free

**Email:** <asemshahen5@gmail.com>

## License
GPL-3.0-or-later. See [LICENSE](LICENSE).
