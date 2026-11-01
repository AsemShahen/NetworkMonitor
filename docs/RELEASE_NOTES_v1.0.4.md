# Network Monitor 1.0.4

Network Monitor shows live download and upload speeds for every Linux
application, with real application blocking through cgroup v2 + nftables and a
polkit-authenticated helper. The interface is bilingual English/Arabic with
full RTL support and defaults to English.

## Highlights

- Live per-process download and upload rates.
- Active connections, executable paths, and session totals.
- Interactive time-series traffic chart.
- Search, sortable columns, hide-idle filter, and export.
- Real block/unblock with cgroup v2 + nftables and polkit.
- Persistent blocklist with import/export and apply-on-start.
- Light theme by default, automatic dark mode, and a manual theme setting.
- Tray icon, desktop integration, and full RTL layout.
- GPL-3.0-or-later; local-first, no account or telemetry.

## Changes in 1.0.4

- The default theme now follows the system color scheme. Light mode is used
  when the system is not dark, including minimal Xvfb environments such as the
  AppImageHub test runner. Dark mode is used only when the system reports a
  dark color scheme, or when the user selects **Dark** in Settings.
- Added a **Theme** setting with **Follow system**, **Light**, and **Dark**
  options. The selection is saved and applied immediately.
- The AppImage now embeds `gh-releases-zsync` update information and publishes
  `NetworkMonitor-1.0.4-x86_64.AppImage.zsync` next to the AppImage. Users can
  update with AppImageUpdate or similar tools.
- The AppImageHub catalog test passed on v1.0.4 with no warnings. Version
  1.0.4 resolves the two v1.0.3 follow-up warnings: dark default theme and
  missing AppImage update information.

## Packages

- `network-monitor_1.0.4_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.4-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.4-x86_64.AppImage` — portable
- `NetworkMonitor-1.0.4-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `SHA256SUMS` — release asset checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.4>

### Signed APT/RPM repository

The signed repository is published at
<https://asemshahen.github.io/NetworkMonitor/> and serves the official
`v1.0.4` assets. The `v1.0.4` packages are attached to this GitHub release and
match the release's `SHA256SUMS`. The repository fingerprint is:

```text
Network Monitor packages <asemshahen5@gmail.com>
Fingerprint: D53CB321C38875CCA82128CC77EED1C545319AE8
```

> If you added the repository before 2026-10-28, re-import the public key with
> the APT/RPM commands in the install guide. The previous key was lost and has
> been replaced.

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
v1.0.4 AppImage starts in light mode on non-dark systems and includes update
information. A `/retest` comment will re-run the catalog test.

## Notes

- The `.deb` and `.rpm` install the privileged helper and polkit policy.
- The AppImage bundles the helper, but blocking still requires host `pkexec`,
  `python3`, `nftables`, and cgroup v2.
- The release assets are built by the GitHub Actions workflow on Ubuntu 22.04.
  The signed package repository serves the same official assets.

## العربية

يعرض Network Monitor سرعة التنزيل والرفع اللحظية لكل تطبيق على لينكس، مع حظر
فعلي عبر cgroup v2 وnftables ومساعد محمي بـpolkit. الواجهة إنجليزية وعربية
مع دعم RTL كامل، والافتراضي إنجليزي.

### التغييرات في 1.0.4

- أصبح المظهر الافتراضي يتبع نظام التشغيل. يُستخدم المظهر الفاتح عندما لا
  يكون النظام داكنًا، بما في ذلك بيئات Xvfb البسيطة مثل بيئة اختبار
  AppImageHub. لا يُستخدم المظهر الداكن إلا إذا أبلغ النظام عن مظهر داكن أو
  اختار المستخدم **داكن** من الإعدادات.
- أُضيف إعداد **المظهر** بخيارات **حسب النظام** و**فاتح** و**داكن**، ويُحفظ
  الاختيار ويُطبَّق فورًا.
- أصبح AppImage يضم معلومات تحديث `gh-releases-zsync` وينشر ملف
  `NetworkMonitor-1.0.4-x86_64.AppImage.zsync` بجانب AppImage، ليعمل التحديث
  عبر AppImageUpdate والأدوات المشابهة.
- نجح اختبار دليل AppImageHub على v1.0.4 دون تحذيرات، ويعالج الإصدار التحذيرين
  السابقين: المظهر الداكن الافتراضي وغياب معلومات تحديث AppImage.

### الحزم

- `network-monitor_1.0.4_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.4-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.4-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.0.4-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `SHA256SUMS` — بصمات أصول الإصدار

### مستودع APT/RPM الموقّع

<https://asemshahen.github.io/NetworkMonitor/>

يخدم المستودع الموقّع أصول الإصدار `v1.0.4` الرسمية. حزم `v1.0.4` مرفقة
بهذا الإصدار وتطابق `SHA256SUMS`. بصمة المفتاح:

```text
D53CB321C38875CCA82128CC77EED1C545319AE8
```

> إذا أضفت المستودع قبل 2026-10-28، فأعد استيراد المفتاح العام بالأوامر
> الموجودة في دليل التثبيت. المفتاح السابق فُقد واستُبدل بمفتاح جديد.

أوامر APT وRPM موجودة في [دليل التثبيت](https://github.com/AsemShahen/NetworkMonitor/blob/main/docs/INSTALL.md).

### AUR

اسم حزمة AUR هو `network-monitor-qt-bin` (بانتظار القبول). الاسم
`network-monitor-bin` يخص مشروعًا آخر.

### AppImageHub

طلب PR بملف واحد: <https://github.com/AppImage/appimage.github.io/pull/10786>.
يبدأ AppImage 1.0.4 بالمظهر الفاتح على الأنظمة غير الداكنة ويضم معلومات
التحديث. سيؤدي تعليق `/retest` إلى إعادة اختبار الدليل.

## Author

**Author:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free

**Email:** <asemshahen5@gmail.com>
