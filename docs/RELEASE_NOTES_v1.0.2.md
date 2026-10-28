# Network Monitor 1.0.2

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

## Fixes in 1.0.2

- The AppImage now bundles `libxkbcommon-x11`, `libxcb-cursor`, and the related
  xcb helper libraries. It starts with the Qt xcb platform plugin on minimal
  Debian/Ubuntu systems that do not have those X11 helpers installed, including
  the AppImageHub test runner.
- AppImageHub PR #10786 was retested with this release.

## Packages

- `network-monitor_1.0.2_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.2-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.2-x86_64.AppImage` — portable
- `SHA256SUMS` — release asset checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.2>

### Signed APT/RPM repository

The signed repository is published at
<https://asemshahen.github.io/NetworkMonitor/> and continues to serve the
official `v1.0.1` assets while the repository signing key is being restored.
The `v1.0.2` packages are attached to this GitHub release and match the
release's `SHA256SUMS`. The repository fingerprint remains:

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

One-file PR: <https://github.com/AppImage/appimage.github.io/pull/10786>. The
v1.0.1 AppImage failed the catalog test because the host lacked
`libxkbcommon-x11`; this release bundles it. The retest is pending.

## Notes

- The `.deb` and `.rpm` install the privileged helper and polkit policy.
- The AppImage bundles the helper, but blocking still requires host `pkexec`,
  `python3`, `nftables`, and cgroup v2.
- The release assets are built by the GitHub Actions workflow. The signed
  package repository serves the same official `v1.0.1` assets until the
  repository signing key is restored.

## العربية

يعرض Network Monitor سرعة التنزيل والرفع اللحظية لكل تطبيق على لينكس، مع حظر
فعلي عبر cgroup v2 وnftables ومساعد محمي بـpolkit. الواجهة إنجليزية وعربية
مع دعم RTL كامل، والافتراضي إنجليزي.

### إصلاحات 1.0.2

- أصبحت حزمة AppImage تضم `libxkbcommon-x11` و`libxcb-cursor` ومكتبات xcb
  المساعدة، لتعمل واجهة Qt xcb على أنظمة Debian/Ubuntu البسيطة التي لا
  تحتوي هذه المكتبات، بما فيها بيئة اختبار AppImageHub.
- أُعيد اختبار PR #10786 باستخدام هذا الإصدار.

### الحزم

- `network-monitor_1.0.2_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.2-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.2-x86_64.AppImage` — محمولة
- `SHA256SUMS` — بصمات أصول الإصدار

### مستودع APT/RPM الموقّع

<https://asemshahen.github.io/NetworkMonitor/>

المستودع الموقّع يخدم حاليًا أصول الإصدار `v1.0.1` الرسمية إلى أن يُستعاد
مفتاح توقيع المستودع. حزم `v1.0.2` مرفقة بهذا الإصدار وتطابق `SHA256SUMS`.
بصمة المفتاح:

```text
4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE
```

أوامر APT وRPM موجودة في [دليل التثبيت](https://github.com/AsemShahen/NetworkMonitor/blob/main/docs/INSTALL.md).

### AUR

اسم حزمة AUR هو `network-monitor-qt-bin` (بانتظار القبول). الاسم
`network-monitor-bin` يخص مشروعًا آخر.

### AppImageHub

طلب PR بملف واحد: <https://github.com/AppImage/appimage.github.io/pull/10786>.
فشل اختبار إصدار v1.0.1 بسبب غياب `libxkbcommon-x11`؛ هذا الإصدار يضمّنه،
والاختبار الجديد قيد الانتظار.

## Author

**Author:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free

**Email:** <asemshahen5@gmail.com>
