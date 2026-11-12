# Official publishing channels

This document separates official distribution repositories from app stores,
and records what is ready, what needs an account, and what needs human review.
Do not describe a channel as live until the responsible service accepts it.

## Current status

| Channel | Type | Status | Remaining work |
|---|---|---|---|
| GitHub Releases | direct release | `v1.1.0` published | none |
| GitHub Discussions | community forum | enabled | announcement posted |
| AppImageHub | app catalog | published; 1.1.0 retest pending | none |
| Signed APT/RPM repository on GitHub Pages | third-party signed repository | live; serves `v1.1.0` | none |
| AUR | community repository | `1.1.0` files ready, not published | no AUR account yet; registration is behind an anti-bot challenge |
| Official Debian | distribution repository | source accepted by Mentors; RFS bug `1153391` open | Debian sponsor |
| Official Fedora | distribution repository | review bug `2568606` filed; 1.1.0 spec and SRPM attached; `fedora-review?` set | package reviewer and sponsor |
| Snap Store | app store | name `network-monitor-desktop` reserved | choose confinement architecture and pass manual review |
| Flathub | app store | not suitable yet | sandbox redesign and Flathub policy compliance |

## GitHub Discussions

GitHub Discussions is enabled for release announcements and user questions.
The 1.1.0 announcement is posted in the Announcements category:

<https://github.com/AsemShahen/NetworkMonitor/discussions/2>

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
containers. The 1.1.0 main-branch run passed for both jobs after the Debian
container installs `pybuild-plugin-pyproject`, including the AppStream and
desktop-file checks. The tag run was created before that CI fix and failed only
on the missing Debian build dependency.

### Current submission state

The Debian source package was accepted by Debian Mentors:

- Upload: `network-monitor 1.0.9-3`, uploaded 2026-11-08 02:07 UTC.
- Package page: <https://mentors.debian.net/package/network-monitor/>
- The source tree now contains a prepared `1.1.0-1` entry for the next upload.
- Sponsor status: **needs a sponsor**.
- The package is not in the Debian archive yet.
- RFS bug: <https://bugs.debian.org/1153391> (open, wishlist).
- The RFS email was sent from `asemshahen5@gmail.com` to
  `submit@bugs.debian.org` on 2026-11-08. See `docs/DEBIAN_RFS.md` for the
  template; the sent message is preserved in `docs/DEBIAN_RFS.eml`.

The Fedora review request is filed:

- Bug: <https://bugzilla.redhat.com/show_bug.cgi?id=2568606>
- Source RPM:
  <https://github.com/AsemShahen/NetworkMonitor/releases/download/v1.1.0/network-monitor-1.1.0-1.fc45.src.rpm>
- Source RPM SHA-256:
  `60fb8a4453b9ebc785175f77386579bd1427485bfa83405f662db366c5335013`
- Status: `NEW`, with `fedora-review?` requested; the bug description and latest
  comment `19295882` include the 1.1.0 spec/SRPM URLs. Waiting for a Fedora
  package reviewer and sponsor.
- `fedora-review-service` was triggered with the public source RPM URL.
- The Fedora spec in the source tree is 1.1.0. The package remains blocked by
  `FE-NEEDSPONSOR`. The source RPM is a review artifact, not part of
  `SHA256SUMS`, and is ignored by the in-app updater.

### Required user actions

1. Monitor Debian RFS bug `1153391` and answer reviewer comments. A Debian
   sponsor is still required.
2. Monitor Fedora bug `2568606` and answer reviewer comments. A Fedora reviewer
   and sponsor are still required.
3. The Debian Salsa account request was rejected on 2026-11-12. This does not
   reject the package or the RFS; Salsa is optional for Mentors-based review.
   Appeal via `salsa-admin@debian.org` or `#salsa` on OFTC/Matrix. The old
   `salsa@debian.org` address bounces. Do not create a duplicate account.
4. AUR registration currently presents an anti-bot challenge. Create an
   account in a browser when available, then upload `packaging/aur/`.

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
