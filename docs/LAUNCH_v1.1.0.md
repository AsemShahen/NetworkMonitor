# Network Monitor 1.1.0 launch kit

Ready-to-post drafts for Linux communities. Use one community at a time,
disclose that you are the author, answer questions, and do not cross-post the
same text everywhere on the same day.

## Facts

- **Release:** <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>
- **Repository:** <https://github.com/AsemShahen/NetworkMonitor>
- **License:** GPL-3.0-or-later
- **Author:** AL-Asem Software By Asem Shahen
- **New tab:** **Security & Threats** / **الأمان والتهديدات**
- **Packages:** `.deb`, `.rpm`, AppImage, manual `/opt` tarball
- **Repository:** <https://asemshahen.github.io/NetworkMonitor/> (signed APT/RPM repository)
- **Screenshots:** refreshed 1.1.0 gallery at
  <https://github.com/AsemShahen/NetworkMonitor#a-visual-tour-of-110>
  (live activity, usage, security, blocked apps, settings, English/Arabic)
- **Fedora review artifact:**
  <https://github.com/AsemShahen/NetworkMonitor/releases/download/v1.1.0/network-monitor-1.1.0-1.fc45.src.rpm>

## One-line pitch

> Network Monitor shows accurate per-application bandwidth on Linux, keeps
> monthly usage, and now adds a Security & Threats tab with local heuristics,
> optional IP/file reputation checks, and confirmed nftables blocking.

## Short description

Network Monitor is a light/dark, bilingual (English/Arabic) desktop monitor for
Debian/Ubuntu and Fedora. It uses native Netlink counters for accurate
per-application download/upload rates, with `ss` and `/proc/net` fallbacks. It
shows active connections, executable paths, CPU/RSS, session totals, monthly
and daily usage, and an interactive traffic chart. Blocking is real: a
polkit-authenticated helper applies cgroup v2 and nftables rules, with a
persistent blocklist and import/export.

Version 1.1.0 adds the **Security & Threats** tab. It highlights temporary
executable paths, common mining ports, and upload spikes locally. Optionally,
with your own API keys, it can check remote IPs through AbuseIPDB/VirusTotal and
executable hashes through MalwareBazaar/VirusTotal. Results are cached in a
local SQLite database, and remote IPs can be blocked after confirmation.

It is local-first: local checks need no account or cloud service. The interface
defaults to English and switches instantly to Arabic with full RTL support.

## Show HN

**Title:** Show HN: Network Monitor – per-app bandwidth and a new security tab for Linux

**Body:**

I built Network Monitor because I wanted to see which Linux application was
using the network, not just the total interface speed.

It shows live per-process download/upload rates, active connections,
executable paths, session totals, and a time-series chart. You can search,
sort, hide idle processes, and export the visible names. Blocking is not a
mock: it uses cgroup v2 and nftables through a polkit-authenticated helper,
with a persistent blocklist and import/export.

The new 1.1.0 release adds a Security & Threats tab. Local heuristics flag
executables running from temporary paths, connections to common mining ports,
and upload spikes. If you add your own API keys, it can also check remote IPs
through AbuseIPDB/VirusTotal and file hashes through MalwareBazaar/VirusTotal.
Results are cached locally in SQLite, and remote IPs can be blocked after
confirmation. Local checks work offline; there is no telemetry.

The UI is bilingual English/Arabic with full RTL support and defaults to
English. It is GPL-3.0-or-later and reads `/proc` locally.

Packages: `.deb`, `.rpm`, and `.AppImage` on GitHub Releases. A signed APT/RPM
repository is available on GitHub Pages. I would especially appreciate
feedback on the security heuristics, packaging, Fedora/RHEL compatibility, and
the blocking helper.

## Reddit

Use the version that fits each community; do not post the same text to every
subreddit at once. Mention that you are the author.

### r/linux

**Title:** Network Monitor 1.1.0: per-app bandwidth monitor with a new security tab

I released Network Monitor 1.1.0, a GPL-3.0-or-later desktop app for Linux. It
uses native Netlink counters to show accurate per-application download/upload
speeds, connections, executable paths, session totals, and monthly/daily usage.
It can block apps with cgroup v2 + nftables via polkit, and the UI is
English/Arabic with RTL support.

The new release adds a Security & Threats tab: local heuristics for temporary
executable paths, common mining ports, and upload spikes; optional
AbuseIPDB/VirusTotal IP checks; SHA-256 file checks through
MalwareBazaar/VirusTotal; local SQLite caching; and confirmed IP blocking. Local
checks work without API keys.

Packages: `.deb`, `.rpm`, and `.AppImage`.
Source and release notes:
<https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

I am looking for feedback on the security heuristics, packaging, and which
distro/desktop combinations need more testing.

### r/linuxapps

**Title:** Network Monitor 1.1.0 – per-app bandwidth, security findings, and nftables blocking

Network Monitor is a local-first Linux desktop app for per-application network
usage. Version 1.1.0 adds a Security & Threats tab with local heuristics,
optional IP and file reputation checks, and confirmed IP blocking. The main
monitor uses Netlink counters, keeps monthly/daily usage, and supports a signed
in-app updater for GitHub packages.

The UI is English/Arabic with RTL, and the app is GPL-3.0-or-later. Screenshots
and downloads:
<https://github.com/AsemShahen/NetworkMonitor#a-visual-tour-of-110>

### r/Ubuntu

**Title:** Network Monitor 1.1.0 for Ubuntu: per-app bandwidth + security tab (deb)

I published Network Monitor 1.1.0 for Ubuntu/Debian. It shows accurate
per-app download/upload rates with Netlink, keeps monthly/daily usage, and adds
a Security & Threats tab with local heuristics, optional reputation checks, and
confirmed nftables IP blocking.

There is a `.deb` on GitHub Releases and a signed APT repository on GitHub
Pages. Install instructions and the refreshed screenshot gallery:
<https://github.com/AsemShahen/NetworkMonitor#a-visual-tour-of-110>

### r/Fedora

**Title:** Network Monitor 1.1.0 RPM: per-app bandwidth + security findings

I published a Fedora/RHEL RPM for Network Monitor 1.1.0, a per-application
bandwidth monitor with real blocking through cgroup v2 + nftables and polkit.
The new Security & Threats tab adds local heuristics, optional IP/file
reputation checks, and confirmed IP blocking. The UI is English/Arabic with
RTL support, and the in-app updater verifies signed release checksums.

RPM: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>
Signed RPM repository: <https://asemshahen.github.io/NetworkMonitor/>

Feedback on Fedora packaging and SELinux/nftables behavior is welcome.

### r/archlinux

**Title:** network-monitor-qt-bin 1.1.0: per-app bandwidth monitor with security tab

I updated the AUR package `network-monitor-qt-bin` for Network Monitor 1.1.0.
It unpacks the official `.deb` and installs the app, helper, polkit policy,
icons, and desktop file. The new release adds a Security & Threats tab with
local heuristics, optional IP/file reputation checks, and confirmed IP
blocking.

Upstream: <https://github.com/AsemShahen/NetworkMonitor>
AUR: `yay -S network-monitor-qt-bin` (once accepted)

The name is different from the existing `network-monitor-bin`, which belongs to
another project.

### r/ArabicLinux / Arabic communities

**Title:** مراقب الشبكة 1.1.0: راقب استهلاك كل تطبيق واحظره على لينكس

أصدرت Network Monitor 1.1.0، تطبيقًا مفتوح المصدر (GPL-3.0-or-later)
لمراقبة سرعة التنزيل والرفع لكل تطبيق على لينكس، مع حظر فعلي عبر cgroup v2
وnftables ومصادقة polkit. يضيف الإصدار الجديد تبويب **الأمان والتهديدات**:
فحص محلي للمسارات المؤقتة ومنافذ التعدين وارتفاعات الرفع، وفحص اختياري لسمعة
عناوين IP وبصمات الملفات باستخدام مفاتيح API الخاصة بك، وذاكرة SQLite محلية،
وحظر مؤكد لعناوين IP.

الواجهة إنجليزية وعربية مع دعم RTL كامل، والافتراضي إنجليزي. الحزم: `.deb`
و`.rpm` و`.AppImage`، ومستودع APT/RPM موقّع.
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

**Subject:** `Network Monitor 1.1.0: per-app bandwidth + security findings for Linux`

**Body:**

> Network Monitor 1.1.0 is a GPL-3.0-or-later desktop app for Linux that uses
> native Netlink counters for accurate per-application download/upload speeds,
> stores monthly/daily usage, and can block selected apps with cgroup v2 +
> nftables through a polkit helper. The new Security & Threats tab adds local
> heuristics for temporary executable paths, mining ports, and upload spikes,
> plus optional AbuseIPDB/VirusTotal IP checks, SHA-256 file checks through
> MalwareBazaar/VirusTotal, local SQLite caching, and confirmed IP blocking.
> It ships as `.deb`, `.rpm`, and `.AppImage`, has a signed APT/RPM repository,
> and a bilingual English/Arabic UI with RTL support. Screenshots and release
> notes: https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0

## Forum follow-ups

### Fedora Discussion

Suggested category: Fedora Discussion → Fedora Engineering or Ask Fedora,
depending on the community rules.

**Title:** Network Monitor 1.1.0 RPM – feedback on nftables/SELinux behavior

Network Monitor is a per-application bandwidth monitor with real blocking
through cgroup v2 + nftables and polkit. The Fedora source spec is in the
upstream tree and the review request is Fedora bug `2568606`; the 1.1.0 source
RPM is attached to the release. The 1.1.0 release adds a Security & Threats tab
with local heuristics and optional reputation checks. I am looking for feedback
on the RPM, nftables rules, and SELinux behavior. RPM, source RPM, and release
notes:
<https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

### Debian forums / Debian user list

**Subject:** Network Monitor 1.1.0 – per-app bandwidth and security tab

Network Monitor is a GPL-3.0-or-later Qt/PySide6 application for Debian and
Ubuntu. It shows per-application traffic with Netlink, keeps monthly usage, and
can block apps with cgroup v2 + nftables through a polkit helper. The 1.1.0
release adds a Security & Threats tab with local heuristics and optional
IP/file reputation checks. The source package is prepared for Debian and the
RFS is Debian bug `1153391`. Feedback on the package and the security tab is
welcome: <https://github.com/AsemShahen/NetworkMonitor>

### Ubuntu Discourse

**Title:** Network Monitor 1.1.0 – per-app bandwidth and a security tab for Ubuntu

Network Monitor is available as a `.deb` and through a signed APT repository.
Version 1.1.0 adds a Security & Threats tab with local heuristics, optional
AbuseIPDB/VirusTotal checks, SHA-256 file checks, and confirmed nftables IP
blocking. The app also shows live per-application speeds, monthly usage, and
blocked apps. Screenshots and install instructions:
<https://github.com/AsemShahen/NetworkMonitor#a-visual-tour-of-110>

## Checklist

- [x] Publish the GitHub release and verify all assets.
- [x] Update the signed APT/RPM repository; AUR metadata files are ready but
      cannot be pushed until an AUR account is available.
- [ ] Post one community update, then wait for feedback. Show HN is `[dead]`
      and the r/linux attempt was removed by AutoModerator.
- [x] Send two targeted news tips with the refreshed security screenshot.
- [ ] Answer questions and triage bug reports.
- [x] Do not claim Debian/Fedora official publication before a
      sponsor/reviewer accepts the package.
- [x] Do not create forum accounts automatically; use accounts owned by the
      author and follow each community's self-promotion rules.

## Notes

- Reddit's r/linux AutoModerator removed the earlier post because the account
  had 1 karma. Build account history before retrying, or ask a moderator.
- The existing Show HN thread is
  <https://news.ycombinator.com/item?id=50268737>; post a new Show HN only if
  the release is materially new and the community rules allow it.
- The Arabic launch text is also available in
  `docs/LAUNCH_v1.1.0_AR.md`.
