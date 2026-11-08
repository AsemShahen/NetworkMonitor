# Network Monitor 1.0.9

Network Monitor 1.0.9 is a packaging and distribution release. The desktop
interface and monitoring behavior are unchanged, but the source tree now
contains official Debian and Fedora packaging, and distribution-managed
installations no longer try to replace themselves with a GitHub package.

## Highlights

- **Official Debian source packaging.** The new `debian/` directory builds
  `network-monitor` with Debian-provided Python, PySide6, pyqtgraph, pyroute2,
  and NumPy packages. It installs the blocking helper, PolicyKit policy,
  desktop file, AppStream metadata, icons, and a manual page.
- **Official Fedora source spec.** `packaging/fedora/network-monitor.spec`
  follows the Fedora Python packaging macros and uses distribution packages
  instead of the bundled runtime in the GitHub `.rpm`.
- **Distribution-managed updates.** Official packages install
  `/usr/share/network-monitor/distro-managed`. When a newer upstream version
  exists, the in-app updater shows the version and tells the user to update
  through `apt` or `dnf`; it does not download and install a GitHub package over
  a distribution package.
- **AppStream and desktop integration.** The metadata now includes
  screenshots and developer information, and the source packaging installs a
  `network-monitor(1)` manual page.
- **CI validation.** `.github/workflows/distro-packages.yml` builds and
  validates the Debian and Fedora packages in container jobs on every relevant
  change.
- **Compatible dependency bounds.** The Python requirements now accept the
  pyqtgraph and pyroute2 versions shipped by Debian 13 and current Fedora
  branches. The bundled GitHub runtime still uses its pinned newer versions.
- **No data changes.** The usage database, background collector, Netlink
  collector, blocking rules, and GitHub signed-update paths are unchanged.

## Important status

The Debian and Fedora packaging is prepared and passes CI, but it is **not yet
in the official Debian or Fedora repositories**. The Debian source package is
on Mentors and the RFS is open as Debian bug `1153391`; a sponsor is still
required. The Fedora review request is bug `2568606` with `fedora-review?`
requested; a reviewer and sponsor are still required. See
`docs/PUBLISHING_CHANNELS.md` for the current status.

Flathub and Snap Store publication are not part of this release. Flathub needs
a sandbox-compatible design and a submission authored by the user; Snap Store
needs a decision on whether to use classic confinement with a privileged helper
or ship a monitoring-only variant.

## Updating

Version 1.0.6 and later can install 1.0.9 with **Settings → Application
updates → Check for updates**. The updater verifies `SHA256SUMS` and
`SHA256SUMS.asc` before installing.

For a manual `/opt/network-monitor` install from 1.0.5 or older, install once:

```bash
tar -xzf NetworkMonitor-1.0.9-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

After that, later releases can be installed from the update button.

## Assets

- `network-monitor_1.0.9_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.9-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.9-x86_64.AppImage` — portable
- `NetworkMonitor-1.0.9-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `NetworkMonitor-1.0.9-linux-x86_64.tar.gz` — manual `/opt` updater archive
- `network-monitor-1.0.9-1.fc45.src.rpm` — Fedora source RPM for the package review
- `SHA256SUMS` — release file checksums
- `SHA256SUMS.asc` — detached GPG signature for the checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.9>

Verify the download:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

## Package repositories and catalog

- The signed APT/RPM repository will serve `1.0.9` after the release workflow
  publishes it, with verified `InRelease` and `repomd.xml.asc` metadata.
- The local AUR `network-monitor-qt-bin` metadata must be updated to `1.0.9`
  after the release asset and its SHA-256 checksum are available. Publishing
  still depends on AUR account access.
- AppImageHub keeps the existing catalog entry and the
  `gh-releases-zsync` update information.

## Notes

- Debian and Fedora packages use system libraries. Do not mix an official
  distribution package with the bundled GitHub `.deb` or `.rpm`; use the
  package manager for distribution installs.
- The current AppStream component ID is `network-monitor.desktop`. It passes
  relaxed Fedora validation, but a reverse-DNS ID such as
  `com.networkmonitor.app.desktop` is required before a Flathub submission.
- No telemetry, account information, or application list is sent anywhere.

## العربية

Network Monitor 1.0.9 إصدار تغليف وتوزيع. لا تتغير واجهة سطح المكتب أو سلوك
المراقبة، لكن شجرة المصدر تحتوي الآن على تغليف رسمي لـDebian وFedora، ولم تعد
تثبيتات التوزيعات تحاول استبدال نفسها بحزمة GitHub.

### أبرز التغييرات

- **تغليف Debian رسمي.** يبني مجلد `debian/` الجديد حزمة `network-monitor`
  باستخدام Python وPySide6 وpyqtgraph وpyroute2 وNumPy من Debian. وتثبّت
  مساعد الحظر وسياسة PolicyKit وملف سطح المكتب وبيانات AppStream والأيقونات
  وصفحة دليل.
- **ملف Fedora رسمي.** يتبع `packaging/fedora/network-monitor.spec` وحدات
  تغليف Python في Fedora ويستخدم حزم التوزيعة بدل وقت التشغيل المضمّن في حزمة
  `.rpm` الخاصة بـGitHub.
- **تحديثات يديرها مستودع التوزيعة.** تثبّت الحزم الرسمية العلامة
  `/usr/share/network-monitor/distro-managed`. وعند توفر إصدار أحدث يعرض
  المحدّث الإصدار ويطلب التحديث عبر `apt` أو `dnf`، ولا ينزّل حزمة GitHub
  ويثبّتها فوق حزمة التوزيعة.
- **تكامل AppStream وسطح المكتب.** تتضمن البيانات الآن لقطات شاشة ومعلومات
  المطوّر، ويثبّت تغليف المصدر صفحة دليل `network-monitor(1)`.
- **تحقق في CI.** يبني
  `.github/workflows/distro-packages.yml` حزم Debian وFedora ويتحقق منها داخل
  حاويات عند كل تغيير ذي صلة.
- **حدود اعتماديات متوافقة.** تقبل متطلبات Python إصدارات pyqtgraph وpyroute2
  التي توفرها Debian 13 وفروع Fedora الحالية. ويواصل وقت التشغيل المضمّن في
  GitHub استخدام الإصدارات الأحدث المثبّتة.
- **لا تغيير في البيانات.** لم تتغير قاعدة بيانات الاستهلاك أو جامع الخلفية أو
  جامع Netlink أو قواعد الحظر أو مسارات التحديث الموقّع عبر GitHub.

### حالة مهمة

تغليف Debian وFedora جاهز ويجتاز CI، لكنه **ليس بعد في مستودعات Debian أو
Fedora الرسمية**. حزمة المصدر لـDebian موجودة في Mentors وطلب RFS مفتوح برقم
`1153391`، وما زال مطلوباً راعٍ. طلب مراجعة Fedora مفتوح برقم `2568606` وتم
تعيين `fedora-review?`، وما زال مطلوباً مراجع وراعٍ. راجع
`docs/PUBLISHING_CHANNELS_AR.md` للحالة الحالية.

النشر على Flathub وSnap Store ليس جزءاً من هذا الإصدار. يحتاج Flathub إلى
تصميم متوافق مع العزل وطلب يكتبه المستخدم، ويحتاج Snap Store إلى قرار بين
استخدام `classic` مع مساعد مميز أو نشر نسخة مراقبة فقط.

### التحديث

يمكن للإصدار 1.0.6 وما بعده تثبيت 1.0.9 من
**الإعدادات ← تحديثات التطبيق ← التحقق من التحديثات**. يتحقق المحدّث من
`SHA256SUMS` و`SHA256SUMS.asc` قبل التثبيت.

إذا كان لديك تثبيت يدوي في `/opt/network-monitor` من 1.0.5 أو أقدم، فثبّت مرة
واحدة:

```bash
tar -xzf NetworkMonitor-1.0.9-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

بعد ذلك يمكن تثبيت الإصدارات اللاحقة من زر التحديث.

### الحزم

- `network-monitor_1.0.9_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.9-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.9-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.0.9-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `NetworkMonitor-1.0.9-linux-x86_64.tar.gz` — أرشيف التحديث اليدوي في `/opt`
- `network-monitor-1.0.9-1.fc45.src.rpm` — حزمة مصدر Fedora لطلب المراجعة
- `SHA256SUMS` — بصمات ملفات الإصدار
- `SHA256SUMS.asc` — توقيع GPG منفصل للبصمات

التحميل: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.9>

تحقق من الملفات:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### المستودعات والكتالوج

- سيخدم مستودع APT/RPM الموقّع الإصدار `1.0.9` بعد نشر سير عمل الإصدار، مع
  بيانات `InRelease` و`repomd.xml.asc` التي ستُتحقق منها.
- يجب تحديث بيانات AUR المحلية للحزمة `network-monitor-qt-bin` إلى `1.0.9`
  بعد توفر ملف الإصدار وبصمة SHA-256 الخاصة به. ولا يزال النشر يعتمد على
  الوصول إلى حساب AUR.
- يحتفظ AppImageHub بإدراجه الحالي وبمعلومات تحديث `gh-releases-zsync`.

### ملاحظات

- تستخدم حزم Debian وFedora مكتبات النظام. لا تخلط حزمة توزيعة رسمية مع حزمة
  GitHub المضمّنة `.deb` أو `.rpm`؛ استخدم مدير الحزم لتثبيتات التوزيعة.
- معرّف AppStream الحالي هو `network-monitor.desktop`. يجتاز التحقق المتساهل
  في Fedora، لكنه يحتاج إلى معرّف عكسي مثل `com.networkmonitor.app.desktop`
  قبل التقديم إلى Flathub.
- لا تُرسل أي بيانات تتبع أو معلومات حساب أو قائمة تطبيقات إلى أي جهة.
