# Network Monitor 1.0.7

Network Monitor 1.0.7 adds an optional background collector, so monthly and
daily usage can keep updating after the main window is closed. It is opt-in
from **Settings → Background collection**.

## Highlights

- **Usage collection while the app is closed.** The collector runs as a
  systemd user service and samples traffic in the background. No root access is
  required.
- **One database, one writer.** The GUI and the collector share
  `~/.local/share/network-monitor/usage.db`. An advisory `flock` on
  `usage.db.lock` elects exactly one writer, and the GUI hands the writer role
  to the collector when the service starts. This prevents double-counting and
  keeps SQLite safe when both processes are open.
- **Safe handoff.** When the GUI takes the writer role back, it resets the
  traffic baseline so the first sample after the handoff does not include
  traffic already recorded by the collector.
- **Generated user service.** The service unit and launcher are generated at
  runtime for manual `/opt`, `.deb`, `.rpm`, AppImage, and Flatpak
  installations. The AppImage path is refreshed whenever the application
  starts.
- **Status and control in Settings.** Shows whether the collector is running,
  starting, stopped, blocked, or failed, with the last heartbeat time. Enable
  or disable it with one checkbox.
- **No surprise background service.** Background collection is disabled by
  default. Without it, monthly and daily usage is counted only while Network
  Monitor is running.

## How it works

When enabled, the application writes:

- `~/.config/systemd/user/network-monitor-collector.service` — the systemd user
  unit.
- `~/.local/share/network-monitor/collector-launcher.sh` — a small launcher
  that points at the current installation.
- `~/.local/share/network-monitor/collector.json` — a heartbeat and status file
  used by the Settings tab.

The collector starts with the user session, samples every five seconds, groups
traffic by the same application keys as the GUI (including Flatpak, Snap, and
AppImage grouping), and writes monthly and daily totals to the shared database.
It does not collect while `keep_usage` is disabled.

The same monthly table, daily chart, and CSV export are used whether the data
was recorded by the GUI or by the background collector.

## Requirements

The background collector needs a working systemd user session. If systemd is
not available, the setting is disabled and the application keeps counting usage
while it is open. The collector does not need `pkexec` or root access.

## Updating

Version 1.0.6 and later can install 1.0.7 with **Settings → Application
updates → Check for updates**. The updater verifies `SHA256SUMS` and
`SHA256SUMS.asc` before installing.

For a manual `/opt/network-monitor` install from 1.0.5 or older, install once:

```bash
tar -xzf NetworkMonitor-1.0.7-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

After that, later releases can be installed from the update button.

## Assets

- `network-monitor_1.0.7_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.7-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.7-x86_64.AppImage` — portable
- `NetworkMonitor-1.0.7-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `NetworkMonitor-1.0.7-linux-x86_64.tar.gz` — manual `/opt` updater archive
- `SHA256SUMS` — release file checksums
- `SHA256SUMS.asc` — detached GPG signature for the checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.7>

Verify the download:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

## Notes

- The collector reports status through `collector.json`; if its heartbeat is
  stale, Settings shows it as stopped.
- If the GUI and collector cannot hand off the writer role, the Settings tab
  shows a clear error. Restarting Network Monitor retries the handoff.
- Reset monthly usage from the Usage tab. When the collector owns the writer
  role, the app briefly stops the service, performs the reset, and starts it
  again.
- Flatpak background collection depends on the host's systemd user session and
  the Flatpak sandbox permissions. If it is unavailable, the checkbox is
  disabled and the app falls back to counting while open.
- No telemetry, account information, or application list is sent anywhere.

## العربية

يضيف Network Monitor 1.0.7 جامع خلفية اختيارياً، بحيث يستمر تحديث الاستهلاك
الشهري واليومي بعد إغلاق النافذة الرئيسية. يُفعَّل من
**الإعدادات ← الجمع في الخلفية**.

### أبرز الميزات

- **جمع الاستهلاك أثناء إغلاق التطبيق.** يعمل الجامع كخدمة مستخدم في systemd
  ويأخذ عينات من الحركة في الخلفية. لا يحتاج صلاحيات الجذر.
- **قاعدة بيانات واحدة وكاتب واحد.** تشترك الواجهة والجامع في
  `~/.local/share/network-monitor/usage.db`. يفرض قفل `flock` استشاري على
  `usage.db.lock` كاتباً واحداً فقط، وتسلّم الواجهة دور الكتابة إلى الجامع عند
  بدء الخدمة. يمنع ذلك الاحتساب المزدوج ويحافظ على سلامة SQLite عند فتح
  العمليتين.
- **تسليم آمن لدور الكتابة.** عند استعادة الواجهة لدور الكتابة تعيد ضبط خط
  الأساس، فلا تتضمن أول عينة حركة سجّلها الجامع مسبقاً.
- **خدمة مستخدم مولّدة تلقائياً.** تُولَّد وحدة الخدمة والمشغّل وقت التشغيل
  لتثبيتات `/opt` اليدوية و`.deb` و`.rpm` وAppImage وFlatpak. يُحدَّث مسار
  AppImage عند كل تشغيل للتطبيق.
- **الحالة والتحكم من الإعدادات.** تظهر حالة الجامع: يعمل، يبدأ، متوقف،
  بانتظار تحرير القاعدة، أو حدث خطأ، مع وقت آخر نبضة. يمكن تفعيله أو تعطيله
  بخيار واحد.
- **لا خدمة خلفية مفاجئة.** الجمع في الخلفية معطّل افتراضياً. وبدونه يُحسب
  الاستهلاك الشهري واليومي أثناء تشغيل Network Monitor فقط.

### آلية العمل

عند التفعيل يكتب التطبيق:

- `~/.config/systemd/user/network-monitor-collector.service` — وحدة مستخدم
  systemd.
- `~/.local/share/network-monitor/collector-launcher.sh` — مشغّل صغير يشير إلى
  التثبيت الحالي.
- `~/.local/share/network-monitor/collector.json` — ملف نبضة وحالة تقرأه
  الإعدادات.

يبدأ الجامع مع جلسة المستخدم، ويأخذ عينة كل خمس ثوانٍ، ويجمع الحركة حسب مفاتيح
التطبيقات نفسها التي تستخدمها الواجهة (بما في ذلك تجميع Flatpak وSnap
وAppImage)، ويكتب الإجماليات الشهرية واليومية في قاعدة البيانات المشتركة. لا
يجمع البيانات عندما يكون `keep_usage` معطّلاً.

تُستخدم جداول الشهر والرسم اليومي وتصدير CSV نفسها سواء سجّلت البيانات
الواجهة أو جامع الخلفية.

### المتطلبات

يحتاج جامع الخلفية إلى جلسة مستخدم systemd عاملة. إذا لم تكن systemd متاحة،
يُعطَّل الخيار ويستمر التطبيق في حساب الاستهلاك أثناء فتحه. لا يحتاج الجامع إلى
`pkexec` أو صلاحيات الجذر.

### التحديث

يمكن للإصدار 1.0.6 وما بعده تثبيت 1.0.7 من
**الإعدادات ← تحديثات التطبيق ← التحقق من التحديثات**. يتحقق المحدّث من
`SHA256SUMS` و`SHA256SUMS.asc` قبل التثبيت.

إذا كان لديك تثبيت يدوي في `/opt/network-monitor` من 1.0.5 أو أقدم، فثبّت مرة
واحدة:

```bash
tar -xzf NetworkMonitor-1.0.7-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

بعد ذلك يمكن تثبيت الإصدارات اللاحقة من زر التحديث.

### الحزم

- `network-monitor_1.0.7_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.7-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.7-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.0.7-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `NetworkMonitor-1.0.7-linux-x86_64.tar.gz` — أرشيف التحديث اليدوي في `/opt`
- `SHA256SUMS` — بصمات ملفات الإصدار
- `SHA256SUMS.asc` — توقيع GPG منفصل للبصمات

التحميل: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.7>

تحقق من الملفات:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### ملاحظات

- يعرض الجامع حالته عبر `collector.json`؛ وإذا تأخرت نبضته تظهره الإعدادات
  متوقفاً.
- إذا تعذّر تسليم دور الكتابة بين الواجهة والجامع، تعرض الإعدادات خطأ واضحاً.
  إعادة تشغيل Network Monitor تعيد المحاولة.
- لإعادة تعيين استهلاك شهر من تبويب الاستهلاك، يوقف التطبيق الخدمة مؤقتاً ثم
  يعيد تشغيلها بعد إعادة التعيين عندما يكون الجامع هو الكاتب.
- يعتمد جمع الخلفية في Flatpak على جلسة systemd في النظام المضيف وأذونات
  العزل. وإذا لم يكن متاحاً يُعطَّل الخيار ويعود التطبيق للحساب أثناء فتحه.
- لا تُرسل أي بيانات تتبع أو معلومات حساب أو قائمة تطبيقات إلى أي جهة.
