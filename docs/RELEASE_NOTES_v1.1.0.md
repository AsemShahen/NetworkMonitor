# Network Monitor 1.1.0

Network Monitor 1.1.0 adds the **Security & Threats** tab: local network
heuristics, optional reputation lookups for remote IP addresses and file
hashes, local caching, and confirmed IP blocking through the existing
polkit-authenticated helper.

## Highlights

- **Security & Threats tab.** A new top-level tab lists findings with severity,
  time, application, PID, remote endpoint, and executable path. Filters and
  context menus make it possible to inspect a finding, scan its IP, hash its
  executable, or block the application/IP.
- **Local heuristics without API keys.** The engine detects executables running
  from temporary paths, connections to common mining-pool ports, and upload
  rates far above an application's baseline. Local findings never leave the
  machine.
- **Optional IP reputation.** AbuseIPDB and VirusTotal checks run in background
  threads so the interface stays responsive. Results are normalized, cached in
  a separate `security.db`, and can be refreshed manually. API keys are stored
  in the local configuration and are sent only to the selected provider.
- **File reputation and SHA-256.** Select an application and check its
  executable by SHA-256 through MalwareBazaar or VirusTotal. Hashes and results
  are cached locally; large files are hashed in chunks.
- **Confirmed blocking.** Remote IPs can be blocked or unblocked through the
  existing cgroup v2 + nftables helper. The helper adds IPs to the
  `network_monitor` nftables table and keeps the existing polkit prompt.
- **Endpoint-aware collection.** Netlink, `ss`, and `/proc/net` collection now
  retain local and remote endpoints, so security findings can be matched to the
  correct process and destination.
- **Bilingual and theme-aware.** All new strings are available in English and
  Arabic, the tables and filters honor RTL, and the tab follows the current
  light/dark theme.
- **Tests.** `tests/test_security.py` covers the heuristics, SQLite cache,
  provider normalization, and file hashing. The full suite passes.

## Privacy

- Local heuristics work offline and do not contact any service.
- Reputation checks are opt-in. Only the selected IP address or SHA-256 hash is
  sent to the selected provider, together with the user's own API key.
- Results are cached locally in `security.db`; no telemetry, account
  information, or application list is uploaded by Network Monitor.
- Blocking still requires the local polkit-authenticated helper and host
  `nftables`; the security tab does not run network requests as root.

## Updating

Version 1.0.6 and later can install 1.1.0 with **Settings → Application
updates → Check for updates**. The updater verifies `SHA256SUMS` and
`SHA256SUMS.asc` before installing.

For a manual `/opt/network-monitor` install from 1.0.5 or older, install once:

```bash
tar -xzf NetworkMonitor-1.1.0-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

After that, later releases can be installed from the update button.

## Assets

- `network-monitor_1.1.0_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.1.0-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.1.0-x86_64.AppImage` — portable
- `NetworkMonitor-1.1.0-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `NetworkMonitor-1.1.0-linux-x86_64.tar.gz` — manual `/opt` updater archive
- `network-monitor-1.1.0-1.fc45.src.rpm` — Fedora source RPM for the package review
- `SHA256SUMS` — release file checksums
- `SHA256SUMS.asc` — detached GPG signature for the checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

Verify the download:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

## Package repositories and catalog

- The signed APT/RPM repository publishes the release assets and signed
  metadata after the release workflow finishes.
- The AUR `network-monitor-qt-bin` metadata is updated after the CI-built
  `.deb` and its SHA-256 checksum are available.
- AppImageHub keeps the existing catalog entry and the
  `gh-releases-zsync` update information.

## Official distribution status

The upstream release is 1.1.0, but the official distribution packages are
still waiting for human sponsors/reviewers:

- **Debian:** the Mentors source package currently in the RFS is
  `network-monitor 1.0.9-3`; Debian bug `1153391` is awaiting a sponsor. The
  source tree now contains a `1.1.0-1` changelog entry for the next upload.
- **Fedora:** bug `2568606` is open with `fedora-review?` and is waiting for a
  reviewer/sponsor. The Fedora spec in the source tree is updated to 1.1.0.
- **Snap:** publication is deferred until the confinement and privileged-helper
  architecture is decided.
- **Flathub:** not part of this release; it needs a sandbox-compatible design
  and a user-authored submission.

The GitHub `.deb`, `.rpm`, AppImage, and manual `/opt` packages are separate
from the official distribution packages. Do not mix an official distribution
package with a bundled GitHub package; use the distribution package manager for
distribution installs.

## Notes

- The new tab is named **Security & Threats** / **الأمان والتهديدات**.
- Reputation providers have their own quotas and terms. Add API keys in
  Settings only if you want online checks.
- The new AppStream screenshot is
  `docs/screenshots/security.png`.
- The full test suite is run with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```

## العربية

يضيف Network Monitor 1.1.0 تبويب **الأمان والتهديدات**: فحصًا محليًا للشبكة،
وفحصًا اختياريًا لسمعة عناوين IP وبصمات الملفات، وذاكرة محلية، وحظرًا مؤكدًا
لعناوين IP عبر المساعد المحمي بـpolkit.

### أبرز التغييرات

- **تبويب الأمان والتهديدات.** يعرض التبويب الجديد النتائج مع الخطورة والوقت
  والتطبيق وPID والعنوان البعيد والمسار التنفيذي. وتتيح المرشحات وقوائم
  السياق فحص العنوان، أو حساب SHA-256 للملف، أو حظر التطبيق/العنوان.
- **فحص محلي دون مفاتيح API.** يكشف المحرك الملفات التنفيذية التي تعمل من
  مسارات مؤقتة، والاتصالات بمنافذ تعدين شائعة، وارتفاعات الرفع الكبيرة مقارنة
  بخط الأساس. لا تغادر نتائج الفحص المحلي الجهاز.
- **سمعة عناوين IP اختيارية.** تعمل فحوص AbuseIPDB وVirusTotal في خيوط
  خلفية كي تبقى الواجهة سريعة. تُطبّع النتائج وتُخزّن في `security.db`
  المنفصل، ويمكن تحديثها يدويًا. تبقى مفاتيح API في الإعدادات المحلية ولا
  تُرسل إلا إلى المزوّد المختار.
- **سمعة الملفات وSHA-256.** اختر تطبيقًا وافحص ملفه التنفيذي عبر SHA-256
  باستخدام MalwareBazaar أو VirusTotal. تُخزّن البصمات والنتائج محليًا،
  وتُحسب الملفات الكبيرة على أجزاء.
- **حظر مؤكد.** يمكن حظر عناوين IP البعيدة أو إلغاء حظرها عبر مساعد
  cgroup v2 + nftables الحالي. يضيف المساعد العناوين إلى جدول nftables باسم
  `network_monitor` ويحافظ على مطالبة polkit الحالية.
- **جمع يعرف العنوانين المحلي والبعيد.** يحتفظ جمع Netlink و`ss` و`/proc/net`
  بالعنوانين المحلي والبعيد، لتُطابق نتائج الأمان العملية والوجهة الصحيحتين.
- **ثنائي اللغة ويراعي الثيم.** كل النصوص الجديدة متاحة بالإنجليزية والعربية،
  والجداول والمرشحات تراعي RTL، ويتبع التبويب الثيم الفاتح/الداكن الحالي.
- **اختبارات.** يغطي `tests/test_security.py` المحرك والذاكرة وتطبيع نتائج
  المزوّدين وحساب بصمة الملفات. وتنجح مجموعة الاختبارات كاملة.

### الخصوصية

- تعمل الفحوص المحلية دون اتصال ولا تتصل بأي خدمة.
- فحوص السمعة اختيارية. يُرسل عنوان IP المحدد أو بصمة SHA-256 فقط إلى المزوّد
  المختار، مع مفتاح API الخاص بالمستخدم.
- تُخزّن النتائج محليًا في `security.db`؛ ولا يرفع Network Monitor أي قياسات
  أو معلومات حساب أو قائمة تطبيقات.
- لا يزال الحظر يحتاج إلى المساعد المحلي المحمي بـpolkit وإلى `nftables` على
  النظام؛ ولا يشغّل تبويب الأمان طلبات الشبكة بصلاحية root.

### التحديث

يمكن للإصدار 1.0.6 وما بعده تثبيت 1.1.0 من
**الإعدادات ← تحديثات التطبيق ← التحقق من التحديثات**. يتحقق المحدّث من
`SHA256SUMS` و`SHA256SUMS.asc` قبل التثبيت.

للتثبيت اليدوي في `/opt/network-monitor` من 1.0.5 أو أقدم، ثبّت 1.1.0 مرة
واحدة:

```bash
tar -xzf NetworkMonitor-1.1.0-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

بعد ذلك يمكن تثبيت الإصدارات اللاحقة من زر التحديث.

### الأصول

- `network-monitor_1.1.0_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.1.0-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.1.0-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.1.0-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `NetworkMonitor-1.1.0-linux-x86_64.tar.gz` — أرشيف التحديث اليدوي في `/opt`
- `network-monitor-1.1.0-1.fc45.src.rpm` — حزمة مصدر Fedora لطلب المراجعة
- `SHA256SUMS` — بصمات ملفات الإصدار
- `SHA256SUMS.asc` — توقيع GPG المنفصل للبصمات

التحميل: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

للتحقق من التنزيل:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### المستودعات والكتالوج

- ينشر مستودع APT/RPM الموقّع أصول الإصدار وبياناته الموقّعة بعد انتهاء سير
  عمل الإصدار.
- تُحدّث بيانات AUR للحزمة `network-monitor-qt-bin` بعد توفر ملف `.deb` الذي
  يبنيه CI وبصمة SHA-256 الخاصة به.
- يحتفظ AppImageHub بمدخله الحالي وبينات تحديث `gh-releases-zsync`.

### حالة التوزيعات الرسمية

الإصدار upstream هو 1.1.0، لكن حزم التوزيعات الرسمية ما زالت تنتظر رعاة
ومراجعين بشريين:

- **Debian:** حزمة المصدر الحالية في Mentors وطلب RFS هي
  `network-monitor 1.0.9-3`؛ والخطأ `1153391` ينتظر راعيًا. تحتوي شجرة المصدر
  الآن على مدخل changelog للإصدار `1.1.0-1` للرفع التالي.
- **Fedora:** الخطأ `2568606` مفتوح مع `fedora-review?` وينتظر مراجعًا وراعيًا.
  وملف Fedora في شجرة المصدر محدّث إلى 1.1.0.
- **Snap:** النشر مؤجل حتى تحديد بنية العزل والمساعد المميز.
- **Flathub:** ليس جزءًا من هذا الإصدار؛ يحتاج تصميمًا متوافقًا مع العزل
  وتقديمًا من المستخدم.

حزم GitHub من `.deb` و`.rpm` وAppImage والتثبيت اليدوي منفصلة عن حزم
التوزيعات الرسمية. لا تخلط حزمة توزيعة رسمية مع حزمة GitHub المضمّنة؛ استخدم
مدير حزم التوزيعة لتثبيتات التوزيعة.

### ملاحظات

- اسم التبويب الجديد هو **الأمان والتهديدات** / **Security & Threats**.
- لمزوّدي السمعة حصص وشروط خاصة بهم. أضف مفاتيح API في الإعدادات فقط إذا
  أردت الفحوص عبر الإنترنت.
- لقطة AppStream الجديدة موجودة في `docs/screenshots/security.png`.
- تُشغّل مجموعة الاختبارات كاملة بالأمر:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
