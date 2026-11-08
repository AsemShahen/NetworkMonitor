# Official publishing channels

This document separates official distribution repositories from app stores,
and records what is ready, what needs an account, and what needs human review.
Do not describe a channel as live until the responsible service accepts it.

## Current status

| Channel | Type | Status | Remaining work |
|---|---|---|---|
| GitHub Releases | direct release | `v1.0.9` published | none |
| AppImageHub | app catalog | published | none |
| Signed APT/RPM repository on GitHub Pages | third-party signed repository | live | none |
| AUR | community repository | files ready, not published | AUR registration is temporarily closed |
| Official Debian | distribution repository | source accepted by Mentors; needs sponsor | RFS email and Debian sponsor |
| Official Fedora | distribution repository | review bug `2568606` filed | package reviewer and sponsor |
| Snap Store | app store | name `network-monitor-desktop` reserved | choose confinement architecture and pass manual review |
| Flathub | app store | not suitable yet | sandbox redesign and Flathub policy compliance |

## Phase 1: Debian and Fedora

The new source packaging uses distribution-provided Python and Qt libraries
instead of the bundled runtime:

- `debian/` for Debian and Ubuntu.
- `packaging/fedora/network-monitor.spec` for Fedora.
- `/usr/share/network-monitor/distro-managed` tells the in-app updater to send
  users to the package manager instead of replacing a distro package with a
  GitHub package.
- `.github/workflows/distro-packages.yml` builds both packages in Debian and
  Fedora containers.

The `distro-packages` workflow builds both packages in Debian and Fedora
containers. The 1.0.9 run passed for both jobs, including the AppStream and
desktop-file checks.

### Current submission state

The Debian source package was accepted by Debian Mentors:

- Upload: `network-monitor 1.0.9-3`, uploaded 2026-11-08 02:07 UTC.
- Package page: <https://mentors.debian.net/package/network-monitor/>
- Sponsor status: **needs a sponsor**.
- The package is not in the Debian archive yet.
- The RFS email must be sent from `asemshahen5@gmail.com` to
  `submit@bugs.debian.org`. See `docs/DEBIAN_RFS.md` for the exact template;
  a ready-to-send message is in `docs/DEBIAN_RFS.eml`.

The Fedora review request is filed:

- Bug: <https://bugzilla.redhat.com/show_bug.cgi?id=2568606>
- Source RPM:
  <https://github.com/AsemShahen/NetworkMonitor/releases/download/v1.0.9/network-monitor-1.0.9-1.fc45.src.rpm>
- Status: `NEW`, waiting for a Fedora package reviewer and sponsor.
- `fedora-review-service` was asked to process the public source RPM URL.

### Required user actions

1. Send the Debian RFS email from `asemshahen5@gmail.com` and monitor the BTS
   bug. A Debian sponsor is still required.
2. Monitor Fedora bug `2568606` and answer reviewer comments. A Fedora reviewer
   and sponsor are still required.
3. The Debian Salsa account still needs manual approval before a Salsa-based
   package repository can be used.
4. AUR registration is temporarily closed; retry later and upload
   `packaging/aur/` when registration reopens.

These channels are the closest route to listing inside GNOME Software, KDE
Discover, and Ubuntu App Center because those stores read the distribution
repositories.

Note: the current AppStream ID is `network-monitor.desktop`, which is not a
reverse-DNS ID. Fedora accepts relaxed validation, but the ID must become
something like `com.networkmonitor.app.desktop` before a Flathub submission.

## Phase 2: Snap Store

The full application needs `/proc`, cgroup v2, and nftables access. The nearest
route is `confinement: classic`, which requires manual Snap Store review.

One of these must be resolved first:

- run the blocking helper as a root snap service and communicate over a local
  socket, or
- publish a monitoring-only variant and document the limitation.

The Snap name `network-monitor` is owned by another publisher. The available
name `network-monitor-desktop` was reserved on 2026-11-08 and is now listed
under Snapcraft → My snaps → Registered snap names. Registrations are subject
to manual review, with a target of 30 days.

A `snapcraft` build and a decision on the privileged-helper architecture are
still required before the first upload.

## Phase 3: Flathub

Flathub is the main Linux app store, but the current architecture is not a
direct fit:

- Flatpak isolates processes, so the UI cannot inspect host applications
  through `/proc` in the way per-application monitoring needs.
- cgroup v2 and nftables blocking needs a host helper outside the normal
  sandbox model.
- Flathub policy explicitly prohibits an AI agent from opening the submission
  PR or generating the manifest and review messages.

The user must author and submit the Flatpak themselves, or a separate
monitoring-only variant must be designed and approved.

## Rule

Do not claim a channel is live before it is accepted. Locally prepared
packaging is not a store listing.
