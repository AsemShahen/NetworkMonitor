# Security & Threats tab

## Design

The tab is split into a Qt-free analysis package and thin Qt adapters:

```
src/netmon/security/
  models.py           Severity findings, IP/file reputation records
  heuristics.py       Local path, mining-port, and upload-spike detection
  cache.py            SQLite cache (IP, file, blocked IPs)
  ip_reputation.py    AbuseIPDB / VirusTotal clients
  file_reputation.py  SHA-256 and MalwareBazaar / VirusTotal clients

src/netmon/gui/
  security_tab.py     Table, cards, filters, details, context menu
  security_workers.py QThread workers for IP and file lookups
```

The core package has no Qt dependency, so it can be tested headlessly and reused
by future CLI tooling.

## Data flow

1. `Controller.snapshot()` collects the same per-application rows and
   `SocketRecord` objects used by the live table.
2. `SecurityEngine.analyze()` runs local heuristics and returns findings plus a
   de-duplicated list of external IP endpoints.
3. `SecurityTab.update_report()` renders the findings on every refresh.
4. Reputation checks run only when requested (or automatically when enabled in
   Settings) in `IPReputationThread` / `FileHashThread`.
5. IP and file results are cached in `$XDG_DATA_HOME/network-monitor/security.db`.
6. The existing privileged helper performs `block_ip` / `unblock_ip` with
   nftables sets in the `network_monitor` table.

## Local heuristics

- Executables running from `/tmp`, `/var/tmp`, or `/dev/shm`.
  AppImage mount paths (`/tmp/.mount_*`) are ignored when the command line
  points to the outer `.AppImage` file.
- Remote TCP/UDP port in `{3333, 4444, 5555, 14444}`.
- Upload rate exceeding the configured floor and a multiple of the recent
  baseline for the same application.

The first snapshot only establishes a baseline; an upload spike is reported on
the next refresh. Findings are de-duplicated by kind/app/endpoint and kept for
the configured retention window.

## Privacy

- Local heuristics never use an API key and never make a network request.
- IP checks send only the IP address to the selected provider.
- File checks send only the SHA-256 digest to MalwareBazaar or VirusTotal.
- API keys stay in the local `config.json` and are not written to the cache.

## Virtual machines

`SecurityEngine` and the live table attribute traffic through host TCP/UDP
sockets. This has two consequences for VirtualBox:

- **NAT mode:** VirtualBox normally proxies guest connections through host
  sockets owned by `VirtualBoxVM` / `VBoxNetNAT`. The app can attribute them
  only if it can read that process's `/proc/<pid>/fd` entries (same user, no
  `hidepid` restriction).
- **Bridged or host-only adapters:** guest packets bypass host sockets. There
  is no host process socket to attribute, so per-process monitoring and the
  local security heuristics cannot see the VM's traffic. Use interface-level
  tools or the VM's own firewall for that mode.

UDP/QUIC traffic has no reliable byte counters through `sock_diag`, so it can
appear as a connection without a useful speed.
