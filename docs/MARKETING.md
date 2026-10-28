# Network Monitor launch kit

Internal marketing and launch checklist. Update the status lines after the
repository, AUR package, and AppImageHub pull request are actually public.
Do not claim a channel is live before it is.

## Facts

- **Name:** Network Monitor
- **Author:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free
- **Email:** <asemshahen5@gmail.com>
- **License:** GPL-3.0-or-later
- **Repository:** <https://github.com/AsemShahen/NetworkMonitor>
- **Release:** <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.1>
- **Package repository:** <https://asemshahen.github.io/NetworkMonitor/> (live)
- **GPG fingerprint:** `4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`
- **AUR:** `network-monitor-qt-bin` (prepared; pending AUR account key and push)
- **AppImageHub:** one-file PR prepared in `packaging/appimagehub/` (pending fork/PR)

## One-line pitch

> Network Monitor shows live download and upload speeds for every Linux
> application, and lets you block any app with cgroup v2 + nftables.

## Short description

Network Monitor is a dark, bilingual (English/Arabic) desktop monitor for
Debian/Ubuntu and Fedora. It shows per-application download/upload rates,
active connections, executable paths, session totals, and an interactive
traffic chart. Blocking is real: a polkit-authenticated helper applies cgroup
v2 and nftables rules, with a persistent blocklist and import/export.

It is local-first: it reads `/proc` and does not need an account or a cloud
service. The interface defaults to English and switches instantly to Arabic
with full RTL support.

## Show HN

**Title:** Show HN: Network Monitor – per-app bandwidth and blocking for Linux

**Body:**

I built Network Monitor because I wanted to see which Linux application was
using the network, not just the total interface speed.

It shows live per-process download/upload rates, active connections,
executable paths, session totals, and a time-series chart. You can search,
sort, hide idle processes, and export the visible names. Blocking is not a
mock: it uses cgroup v2 and nftables through a polkit-authenticated helper,
with a persistent blocklist and import/export.

The UI is bilingual English/Arabic with full RTL support and defaults to
English. It is GPL-3.0-or-later, local-first, and reads `/proc`; there is no
account or telemetry.

Packages: `.deb`, `.rpm`, and `.AppImage` on GitHub Releases. A signed APT/RPM
repository is available on GitHub Pages. I would especially appreciate
feedback on packaging, Fedora/RHEL compatibility, and the blocking helper.

## Reddit

Use the version that fits each community; do not post the same text to every
subreddit at once.

### r/linux

**Title:** Network Monitor: per-app bandwidth monitor with real nftables blocking

I released Network Monitor 1.0.1, a GPL-3.0-or-later desktop app for Linux. It
shows live per-application download/upload speeds, connections, executable
paths, session totals, and a chart. It can block apps with cgroup v2 +
nftables via polkit, and the UI is English/Arabic with RTL support.

It is packaged as `.deb`, `.rpm`, and `.AppImage`. The source and release notes
are here: <https://github.com/AsemShahen/NetworkMonitor>

I am looking for feedback on the packaging and on which distro/desktop
combinations need more testing.

### r/Ubuntu

**Title:** Per-app network monitor with blocking for Ubuntu (deb + signed repo)

I published Network Monitor 1.0.1 for Ubuntu/Debian. It shows per-app
download/upload rates and can block selected applications with cgroup v2 +
nftables through a polkit helper. There is a `.deb` on GitHub Releases and a
signed APT repository on GitHub Pages.

Install instructions and screenshots:
<https://github.com/AsemShahen/NetworkMonitor>

### r/Fedora

**Title:** Network Monitor 1.0.1 RPM: per-app bandwidth and nftables blocking

I published a Fedora/RHEL RPM for Network Monitor, a per-application bandwidth
monitor with real blocking through cgroup v2 + nftables and polkit. The UI is
English/Arabic with RTL support.

RPM: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.1>
Signed RPM repository: <https://asemshahen.github.io/NetworkMonitor/>

Feedback on Fedora packaging and SELinux/nftables behavior is welcome.

### r/archlinux

**Title:** network-monitor-qt-bin: per-app bandwidth monitor with blocking

I prepared an AUR package, `network-monitor-qt-bin`, for Network Monitor. It
unpacks the official `.deb` release and installs the app, helper, polkit
policy, icons, and desktop file.

Upstream: <https://github.com/AsemShahen/NetworkMonitor>
AUR: `yay -S network-monitor-qt-bin` (once accepted)

The name is different from the existing `network-monitor-bin`, which belongs
to another project.

### r/ArabicLinux / Arabic communities

**Title:** مراقب الشبكة: راقب استهلاك كل تطبيق واحظره على لينكس

أصدرت Network Monitor 1.0.1، تطبيقًا مفتوح المصدر (GPL-3.0-or-later)
لمراقبة سرعة التنزيل والرفع لكل تطبيق على لينكس، مع حظر فعلي عبر cgroup v2
وnftables ومصادقة polkit. الواجهة إنجليزية وعربية مع دعم كامل للاتجاه من
اليمين إلى اليسار، والافتراضي إنجليزي.

الحزم: `.deb` و`.rpm` و`.AppImage`، ومستودع APT/RPM موقّع.
المصدر والتنزيل: <https://github.com/AsemShahen/NetworkMonitor>

يسعدني اختباركم على توزيعاتكم، خصوصًا Fedora وArch وopenSUSE.

## Linux news tips

Send a short, factual note with a link and a screenshot to:

- Phoronix: <https://www.phoronix.com/contact>
- OMG! Ubuntu: <https://www.omgubuntu.co.uk/contact>
- It's FOSS: <https://itsfoss.com/contact/>
- Linux Uprising: <https://www.linuxuprising.com/p/contact.html>
- Fedora Magazine: <https://fedoramagazine.org/contribute/>
- Ubuntu Discourse (community news): <https://discourse.ubuntu.com/>

Suggested subject: `Network Monitor 1.0.1: per-app bandwidth + nftables blocking for Linux`

Suggested body:

> Network Monitor 1.0.1 is a GPL-3.0-or-later desktop app for Linux that shows
> live per-application download/upload speeds and can block selected apps with
> cgroup v2 + nftables through a polkit helper. It ships as `.deb`, `.rpm`, and
> `.AppImage`, has a signed APT/RPM repository, and a bilingual English/Arabic
> UI with RTL support. Screenshots and release notes:
> https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.1

## SEO

**Title:** Network Monitor — per-application bandwidth monitor and blocker for Linux

**Meta description:** See live download and upload speeds for every Linux
application, inspect connections, and block apps with cgroup v2 + nftables.
English/Arabic UI, deb/rpm/AppImage, GPL-3.0-or-later.

**Keywords:** Linux network monitor, per-app bandwidth monitor, per-process
network usage, nftables app blocker, cgroup v2 network blocking, Arabic Linux
app, RTL network monitor, Ubuntu network monitor, Fedora network monitor,
AppImage network monitor, open source bandwidth monitor.

Use the GitHub repository description and topics:

`linux`, `network-monitor`, `bandwidth-monitor`, `nftables`, `cgroup-v2`,
`pyside6`, `qt6`, `arabic`, `rtl`, `appimage`, `debian`, `fedora`, `gpl-3-0`.

## Demo video (30–45 seconds)

1. Open on the Live tab. Show two or three applications with changing rates.
2. Switch to Chart and let the graph move.
3. Search for an app, then select it and press **Block selected**.
4. Authenticate with polkit. Show the app in **Blocked apps**.
5. Open **Settings → Language** and switch to Arabic; show the RTL layout.
6. End on the About card with the author and email, then the release URL.

Record at 1366×738 or 1920×1080, 30 fps, no notifications. Use the screenshots
in `docs/screenshots/` as thumbnails.

## Launch checklist

- [x] `gh-pages` branch pushed and Pages enabled.
- [x] `https://asemshahen.github.io/NetworkMonitor/` returns the repository page.
- [x] `apt/dists/stable/InRelease` verifies with the published key.
- [x] `rpm/x86_64/repodata/repomd.xml.asc` verifies with the published key.
- [ ] AUR `network-monitor-qt-bin` pushed and visible.
- [ ] AppImageHub PR opened (one file only) and test comment reviewed.
- [ ] README screenshots render on GitHub.
- [x] Release notes mention the signed repository, AUR, and AppImageHub status.
- [ ] Post Show HN and one subreddit; wait for feedback before cross-posting.
- [ ] Send three Linux news tips with a screenshot.
- [x] Add the repository URL to the GitHub repository homepage field.
