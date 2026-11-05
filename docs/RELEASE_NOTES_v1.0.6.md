# Network Monitor 1.0.6

Network Monitor 1.0.6 adds signed in-app updates. You no longer need to open
GitHub to check, download, or install a new release. The update button is in
**Settings → Application updates**.

## Highlights

- **Check for updates in the app.** Settings checks the official GitHub
  Releases API and selects the correct asset for the current installation.
- **Verified downloads.** Every update downloads `SHA256SUMS` and
  `SHA256SUMS.asc`, verifies the detached GPG signature against the embedded
  public key, then verifies the SHA-256 checksum of the selected asset.
- **Manual `/opt` installs are supported.** The archive
  `NetworkMonitor-<version>-linux-x86_64.tar.gz` is installed through `pkexec`.
  The updater keeps a timestamped backup and automatically restores it if the
  installation fails.
- **AppImage, `.deb`, `.rpm`, and Flatpak are supported.** AppImage files are
  replaced atomically; Debian packages use `apt-get`; RPM packages use
  `dnf` (or `rpm`); Flatpak uses `flatpak update`.
- **Visible progress and clear failures.** The Settings tab and status bar
  show checking, download progress, signature verification, installation, and
  a restart message. Installer output is shown when a command fails.
- **Bilingual update UI.** All update actions, status messages, and errors are
  available in English and Arabic with RTL layout.

## One-time manual installation for older copies

Version 1.0.5 has no updater. If you installed 1.0.5 manually in
`/opt/network-monitor`, install 1.0.6 once using one of these methods:

1. Install the new `.deb`/`.rpm`/AppImage release, or
2. download `NetworkMonitor-1.0.6-linux-x86_64.tar.gz`, extract it, and run:

   ```bash
   tar -xzf NetworkMonitor-1.0.6-linux-x86_64.tar.gz
   sudo ./network-monitor/install.sh
   ```

After 1.0.6 is installed, later releases can be installed from the update
button. The updater also creates a backup directory such as
`/opt/network-monitor.backup-1.0.6-20261105-230000`; it is only used for
rollback and can be removed after a successful restart.

## Security model

The updater trusts only the public key embedded in the application:

```text
Network Monitor packages <asemshahen5@gmail.com>
Fingerprint: D53CB321C38875CCA82128CC77EED1C545319AE8
```

An update is not installed unless:

1. `SHA256SUMS.asc` is a valid detached signature made by that key;
2. the selected asset name is listed in `SHA256SUMS`; and
3. the downloaded file's SHA-256 hash matches the listed value.

`gpg` is required on the host to verify signatures. The release workflow signs
`SHA256SUMS` with the same key used for the signed APT/RPM repository.

## Packages

- `network-monitor_1.0.6_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.6-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.6-x86_64.AppImage` — portable
- `NetworkMonitor-1.0.6-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `NetworkMonitor-1.0.6-linux-x86_64.tar.gz` — manual `/opt` updater archive
- `SHA256SUMS` — release asset checksums
- `SHA256SUMS.asc` — detached GPG signature for the checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.6>

Verify the assets:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

## Notes

- The in-app updater checks GitHub over HTTPS. It does not send telemetry,
  account information, or the application list.
- The `.deb` and `.rpm` updater paths use polkit through `pkexec`; the system
  authentication dialog may appear.
- The AppImage updater replaces the file on disk. Restart the application to
  run the new version. If the AppImage is on a read-only mount, move it to a
  writable directory first.
- Flatpak updates are delegated to `flatpak update` and its existing
  signatures; no `.flatpak` asset is built by this repository yet.
- A source checkout reports that in-app updates are unavailable. Use
  `git pull` or install a release package.
- Monthly usage remains counted only while Network Monitor is running in this
  release. The background collector is planned for 1.0.7.

## العربية

يضيف Network Monitor 1.0.6 تحديثات موقّعة من داخل البرنامج. لم تعد بحاجة إلى
فتح GitHub للتحقق من إصدار جديد أو تنزيله أو تثبيته. يوجد زر التحديث في
**الإعدادات ← تحديثات التطبيق**.

### أبرز الميزات

- **التحقق من التحديثات داخل البرنامج.** تتحقق الإعدادات من واجهة إصدارات
  GitHub الرسمية وتختار الملف المناسب لنوع التثبيت الحالي.
- **تنزيلات موثّقة.** ينزّل التحديث `SHA256SUMS` و`SHA256SUMS.asc`، ويتحقق من
  التوقيع المنفصل بـGPG باستخدام المفتاح العام المضمّن، ثم يتحقق من بصمة
  SHA-256 للملف المختار.
- **دعم التثبيت اليدوي في `/opt`.** يُثبّت الأرشيف
  `NetworkMonitor-<version>-linux-x86_64.tar.gz` عبر `pkexec`، ويحتفظ المحدّث
  بنسخة احتياطية مؤرخة ويسترجعها تلقائياً إذا فشل التثبيت.
- **دعم AppImage و`.deb` و`.rpm` وFlatpak.** يُستبدل AppImage بشكل ذري،
  وتُثبّت حزم Debian عبر `apt-get`، وحزم RPM عبر `dnf` (أو `rpm`)، ويُحدَّث
  Flatpak عبر `flatpak update`.
- **تقدم واضح وأخطاء مفهومة.** يعرض تبويب الإعدادات وشريط الحالة حالات
  التحقق والتنزيل والتحقق من التوقيع والتثبيت ورسالة إعادة التشغيل، ويعرض
  مخرجات المثبّت عند فشل الأمر.
- **واجهة تحديث ثنائية اللغة.** جميع إجراءات التحديث والرسائل والأخطاء متاحة
  بالإنجليزية والعربية مع دعم RTL.

### تثبيت يدوي لمرة واحدة للنسخ القديمة

لا يملك الإصدار 1.0.5 محدّثاً. إذا ثبّت 1.0.5 يدوياً في
`/opt/network-monitor`، فثبّت 1.0.6 مرة واحدة بإحدى الطرق:

1. ثبّت إصدار `.deb` أو `.rpm` أو AppImage الجديد، أو
2. نزّل `NetworkMonitor-1.0.6-linux-x86_64.tar.gz`، وفك ضغطه، ثم نفّذ:

   ```bash
   tar -xzf NetworkMonitor-1.0.6-linux-x86_64.tar.gz
   sudo ./network-monitor/install.sh
   ```

بعد تثبيت 1.0.6 يمكن تثبيت الإصدارات اللاحقة من زر التحديث. ينشئ المحدّث
نسخة احتياطية مثل `/opt/network-monitor.backup-1.0.6-20261105-230000`
تُستخدم للاسترجاع فقط، ويمكن حذفها بعد إعادة تشغيل ناجحة.

### نموذج الأمان

يثق المحدّث فقط بالمفتاح العام المضمّن في التطبيق:

```text
Network Monitor packages <asemshahen5@gmail.com>
Fingerprint: D53CB321C38875CCA82128CC77EED1C545319AE8
```

لا يُثبَّت التحديث إلا إذا:

1. كان `SHA256SUMS.asc` توقيعاً منفصلاً صالحاً بذلك المفتاح؛
2. كان اسم الملف المختار مدرجاً في `SHA256SUMS`؛ و
3. طابقت بصمة SHA-256 للملف المنزّل القيمة المدرجة.

يلزم وجود `gpg` على النظام للتحقق من التوقيعات. يوقّع سير عمل الإصدار
`SHA256SUMS` بالمفتاح نفسه المستخدم لمستودع APT/RPM الموقّع.

### الحزم

- `network-monitor_1.0.6_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.6-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.6-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.0.6-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `NetworkMonitor-1.0.6-linux-x86_64.tar.gz` — أرشيف التحديث اليدوي في `/opt`
- `SHA256SUMS` — بصمات ملفات الإصدار
- `SHA256SUMS.asc` — توقيع GPG منفصل للبصمات

التحميل: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.6>

تحقق من الملفات:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### ملاحظات

- يتحقق المحدّث من GitHub عبر HTTPS، ولا يرسل تتبعاً أو معلومات حساب أو قائمة
  التطبيقات.
- تستخدم مسارات `.deb` و`.rpm` مصادقة polkit عبر `pkexec`، وقد يظهر حوار
  مصادقة النظام.
- يستبدل محدّث AppImage الملف على القرص؛ أعد تشغيل البرنامج لتشغيل الإصدار
  الجديد. إذا كان AppImage على وحدة قراءة فقط، فانقله إلى مجلد قابل للكتابة.
- تُفوَّض تحديثات Flatpak إلى `flatpak update` وتوقيعاته الحالية؛ لا يبني هذا
  المستودع ملف `.flatpak` بعد.
- تعرض نسخة المصدر رسالة بأن التحديث الداخلي غير متاح. استخدم `git pull` أو
  ثبّت حزمة إصدار.
- يبقى الاستهلاك الشهري محسوباً أثناء تشغيل Network Monitor فقط في هذا
  الإصدار. جامع الخلفية مخطط للإصدار 1.0.7.
