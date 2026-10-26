# Network Monitor 1.0.1

Network Monitor shows live download and upload speeds for every Linux
application, with real application blocking through cgroup v2 + nftables and a
polkit-authenticated helper. The interface is bilingual English/Arabic with
full RTL support and defaults to English.

## Highlights

- Live per-process download and upload rates.
- Active connections, executable paths, CPU, RSS, and session totals.
- Interactive time-series traffic chart.
- Search, sortable columns, hide-idle filter, and export.
- Real block/unblock with cgroup v2 + nftables and polkit.
- Persistent blocklist with import/export and apply-on-start.
- Dark theme, tray icon, desktop integration, and full RTL layout.
- GPL-3.0-or-later; local-first, no account or telemetry.

## Packages

- `network-monitor_1.0.1_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.1-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.1-x86_64.AppImage` — portable
- `SHA256SUMS` — release asset checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.1>

### Signed APT/RPM repository

The repository is published at
<https://asemshahen.github.io/NetworkMonitor/>. It serves the official
`v1.0.1` release assets, so its package hashes match `SHA256SUMS`. The
repository metadata is signed with:

```text
Network Monitor packages <asemshahen5@gmail.com>
Fingerprint: 4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE
```

APT:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
echo "deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] https://asemshahen.github.io/NetworkMonitor/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/network-monitor.list
sudo apt update
sudo apt install network-monitor
```

RPM:

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/rpm/network-monitor.repo \
  -o /etc/yum.repos.d/network-monitor.repo
sudo dnf install network-monitor
```

### AUR

The AUR package name is `network-monitor-qt-bin` (submission pending). The
existing `network-monitor-bin` belongs to a different project.

### AppImageHub

A one-file AppImageHub pull request is prepared in
`packaging/appimagehub/`. It is not yet merged into the catalog.

## Notes

- The `.deb` and `.rpm` install the privileged helper and polkit policy.
- The AppImage bundles the helper, but blocking still requires host `pkexec`,
  `python3`, `nftables`, and cgroup v2.
- The release assets are built by the GitHub Actions workflow; the signed
  package repository serves the same official assets. `SHA256SUMS` and the
  signed APT/RPM metadata therefore agree.

## العربية

يعرض Network Monitor سرعة التنزيل والرفع اللحظية لكل تطبيق على لينكس، مع حظر
فعلي عبر cgroup v2 وnftables ومساعد محمي بـpolkit. الواجهة إنجليزية وعربية
مع دعم RTL كامل، والافتراضي إنجليزي.

### أبرز الميزات

- سرعة التنزيل والرفع لكل عملية.
- الاتصالات النشطة، ومسارات الملفات التنفيذية، وCPU وRSS وإجماليات الجلسة.
- رسم بياني زمني تفاعلي.
- بحث وفرز وإخفاء العمليات الخاملة وتصدير.
- حظر/إلغاء حظر فعلي عبر cgroup v2 + nftables وpolkit.
- قائمة حظر دائمة مع استيراد/تصدير وتطبيق عند الإقلاع.
- ثيم داكن، وأيقونة تطبيق، وتكامل مع سطح المكتب، ودعم RTL.
- ترخيص GPL-3.0-or-later؛ يعمل محليًا دون حساب أو تتبّع.

### الحزم

- `network-monitor_1.0.1_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.1-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.1-x86_64.AppImage` — محمولة
- `SHA256SUMS` — بصمات أصول الإصدار

### مستودع APT/RPM الموقّع

<https://asemshahen.github.io/NetworkMonitor/>

المستودع يخدم أصول الإصدار `v1.0.1` الرسمية؛ لذلك تطابق بصمات حزمه
`SHA256SUMS`. بصمة مفتاح التوقيع:

```text
4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE
```

أوامر APT وRPM موجودة في [دليل التثبيت](https://github.com/AsemShahen/NetworkMonitor/blob/main/docs/INSTALL.md).

### AUR

اسم حزمة AUR هو `network-monitor-qt-bin` (بانتظار القبول). الاسم
`network-monitor-bin` يخص مشروعًا آخر.

### AppImageHub

طلب PR بملف واحد جاهز في `packaging/appimagehub/`، ولم يُدمج بعد في الدليل.

## Author

**Author:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free

**Email:** <asemshahen5@gmail.com>
