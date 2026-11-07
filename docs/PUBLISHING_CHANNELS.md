# Official publishing channels

This document separates official distribution repositories from app stores,
and records what is ready, what needs an account, and what needs human review.
Do not describe a channel as live until the responsible service accepts it.

## Current status

| Channel | Type | Status | Remaining work |
|---|---|---|---|
| GitHub Releases | direct release | `v1.0.8` published | none |
| AppImageHub | app catalog | published | none |
| Signed APT/RPM repository on GitHub Pages | third-party signed repository | live | none |
| AUR | community repository | files ready, not published | AUR account and SSH key |
| Official Debian | distribution repository | `debian/` packaging ready | Debian Mentors account and sponsor |
| Official Fedora | distribution repository | `packaging/fedora/` ready | FAS account and review request |
| Snap Store | app store | not started | Snapcraft account and manual review |
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

After pushing, run the `distro-packages` workflow and check the AppStream and
desktop-file validation output.

### Required user actions

1. Create a <https://salsa.debian.org> account and a
   <https://mentors.debian.net> account.
2. Build and sign a Debian source package for Debian Mentors, or ask a Debian
   Developer to sponsor it.
3. Create a Fedora account at <https://accounts.fedoraproject.org>, build an
   `src.rpm`, and open a Fedora `Review Request` in Bugzilla.

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

A Snapcraft account, reservation of the `network-monitor` name, a `snapcraft`
build, and manual review are required.

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
