# Network Monitor

A dark, Arabic-first desktop network monitor for Linux (Debian/Ubuntu and Fedora) that shows per-application download/upload speed and lets you block any application with cgroup v2 + nftables.

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

## Requirements
- Linux with cgroup v2.
- `iproute2` (`ss`) for accurate per-process counters.
- `nftables` + `polkit` (`pkexec`) for blocking.
- Python, PySide6, and pyqtgraph are bundled in the repository.

## Tests
```bash
PYTHONPATH=src python3/bin/python3.14 -m unittest discover -s tests -v
```
