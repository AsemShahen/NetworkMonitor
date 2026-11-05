# Network Monitor 1.0.5

Network Monitor shows accurate live download and upload speeds for every Linux
application, keeps monthly and daily usage statistics, and blocks applications
with cgroup v2 + nftables through a polkit-authenticated helper. The interface
is bilingual English/Arabic with full RTL support and defaults to English.

## Highlights

- Native Netlink per-socket counters (`NETLINK_SOCK_DIAG` via `pyroute2`).
- Automatic `ss` fallback and a final `/proc/net` discovery mode.
- Monthly and daily usage per application, with a chart and CSV export.
- Diagnostics panel with engine, socket attribution, and counter status.
- Flatpak/Snap/AppImage grouping, recent-activity retention, and UDP/QUIC
  “speed unavailable” labels.
- Tray usage access, real tray quit, `--hidden` startup, and optional autostart.
- Light theme by default, automatic dark mode, and a manual theme setting.
- GPL-3.0-or-later; local-first, no account or telemetry.

## Changes in 1.0.5

- **Accurate per-application counters.** The primary engine is now Linux
  Netlink (`NETLINK_SOCK_DIAG`) through `pyroute2` instead of parsing `ss`
  output. This fixes applications such as LM Studio Flatpak that were visible
  in `ss` but fell back to `/proc/net` with no byte counters and therefore
  showed `0 B/s`.
- **Per-inode deltas.** Each socket is tracked by its kernel inode. Closing one
  socket and opening another no longer double-counts or loses bytes. A socket
  created between two samples is counted from its cumulative counters on the
  next sample, while the first sample after startup stays a baseline.
- **Engine fallback order.** Netlink is used first; `ss` is used when Netlink
  is unavailable; `/proc/net` is the last resort for connection discovery and
  clearly reports that byte counters are unavailable.
- **Monthly and daily usage.** A SQLite database stores per-application
  monthly and daily buckets. The new **Usage** tab includes month selection,
  summary cards, a daily download/upload chart, a searchable table, CSV export,
  and a reset action. Usage is counted only while Network Monitor is running.
- **Better application identity.** Flatpak, Snap, and AppImage processes are
  grouped into one application row when enabled. Flatpak scopes are normalized
  across restarts, AppImages use the outer `.AppImage` file, and LM Studio is
  mapped to a readable name.
- **Diagnostics.** The Settings tab now shows the active engine, Netlink and
  `ss` availability, socket counts, how many sockets were attributed to
  processes, and how many UDP/QUIC sockets lack counters. The report can be
  copied to the clipboard.
- **Tray and startup.** The tray menu can open the Usage tab and really quit the
  application. `--hidden` starts minimized when tray support is available, and
  autostart uses the same mode.
- **Clearer limitations.** UDP/QUIC sockets are labeled “speed unavailable”
  instead of showing a misleading `0 B/s`. TCP speeds remain visible when an
  application also has UDP sockets.
- **Arabic/English coverage.** All new usage, diagnostics, grouping, tray, and
  autostart strings are translated, including RTL layout handling.

## Packages

- `network-monitor_1.0.5_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.5-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.5-x86_64.AppImage` — portable
- `NetworkMonitor-1.0.5-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `SHA256SUMS` — release asset checksums
- `SHA256SUMS.asc` — detached GPG signature for the checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.5>

Verify the assets:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### Signed APT/RPM repository

The signed repository is published at
<https://asemshahen.github.io/NetworkMonitor/> and serves the official
`v1.0.5` assets. The repository fingerprint is:

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

## Notes

- The `.deb` and `.rpm` install the privileged helper and polkit policy.
- The AppImage bundles the helper, but blocking still requires host `pkexec`,
  `python3`, `nftables`, and cgroup v2.
- The release packages bundle `pyroute2`. Source installs need
  `python3 -m pip install pyroute2`; without it, the app falls back to `ss`.
- Monthly usage is stored in `~/.local/share/network-monitor/usage.db` and is
  counted only while the application is running.
- UDP/QUIC traffic has no reliable kernel byte counter through sock_diag, so
  those sockets are reported as unmeasured instead of `0 B/s`.
- The release assets are built by the GitHub Actions workflow on Ubuntu 22.04.
  The signed package repository serves the same official assets.
- The test suite covers 23 cases, including `ss` parsing, Netlink attribute
  decoding, cgroup/AppImage identity, SQLite month/day splitting, CSV export,
  reset/prune behavior, configuration defaults, and both languages.

## العربية

يعرض Network Monitor سرعة التنزيل والرفع اللحظية لكل تطبيق على لينكس، ويحفظ
إحصاءات الاستهلاك الشهرية واليومية، ويحظر التطبيقات عبر cgroup v2 وnftables
بمساعد محمي بـpolkit. الواجهة إنجليزية وعربية مع دعم RTL كامل، والافتراضي
إنجليزي.

### أبرز الميزات

- عدّادات Netlink أصلية لكل مقبس عبر `pyroute2`.
- رجوع تلقائي إلى `ss`، ثم `/proc/net` كخيار أخير.
- استهلاك شهري ويومي لكل تطبيق، مع رسم بياني وتصدير CSV.
- لوحة تشخيص تعرض المحرك وحالة العدّادات ونسبة نسب المقابس.
- تجميع Flatpak/Snap/AppImage، والاحتفاظ بالنشاط الأخير، وتسمية UDP/QUIC
  غير المقيسة بوضوح.
- الوصول إلى الاستهلاك من أيقونة النظام، وإغلاق حقيقي منها، وتشغيل
  بـ`--hidden`، وتشغيل تلقائي اختياري.
- المظهر الفاتح افتراضياً، والداكن تلقائياً، مع اختيار يدوي.
- ترخيص GPL-3.0-or-later، محلي بالكامل بلا حساب أو تتبع.

### التغييرات في 1.0.5

- **عدّادات دقيقة لكل تطبيق.** المحرك الأساسي أصبح Netlink
  (`NETLINK_SOCK_DIAG`) عبر `pyroute2` بدل تحليل مخرجات `ss`. يعالج ذلك
  تطبيقات مثل LM Studio Flatpak التي كانت تظهر في `ss` لكن ترجع إلى
  `/proc/net` بلا عدّادات، فتظهر `0 B/s`.
- **فروق لكل inode.** يُتتبع كل مقبس عبر inode الخاص به، فلا تؤدي إغلاق
  مقبس وفتح آخر إلى مضاعفة الاستهلاك أو فقدانه. يُحسب المقبس الجديد من
  عدّاداته التراكمية في العينة التالية، وتبقى العينة الأولى بعد التشغيل
  أساساً.
- **ترتيب الرجوع.** Netlink أولاً، ثم `ss` عند غيابه، ثم `/proc/net` كخيار
  أخير لكشف الاتصالات مع رسالة واضحة أن عدّادات البايت غير متوفرة.
- **استهلاك شهري ويومي.** تُخزَّن البيانات في SQLite، ويضم تبويب
  **الاستهلاك** اختيار الشهر، وبطاقات الملخص، ورسمًا يوميًا، وجدولًا قابلًا
  للبحث، وتصدير CSV، وتصفير الشهر. يُحسب الاستهلاك فقط أثناء تشغيل
  Network Monitor.
- **هوية أفضل للتطبيقات.** تُجمع عمليات Flatpak وSnap وAppImage في صف واحد
  عند التفعيل. تُطبَّع نطاقات Flatpak عبر إعادة التشغيل، ويُستخدم ملف
  `.AppImage` الخارجي، ويظهر LM Studio باسم مقروء.
- **التشخيص.** يعرض تبويب الإعدادات المحرك النشط، وتوفر Netlink و`ss`،
  وعدد المقابس، وعدد المقابس المنسوبة للعمليات، وعدد مقابس UDP/QUIC بلا
  عدّادات، مع زر نسخ.
- **أيقونة النظام والتشغيل.** تفتح أيقونة النظام تبويب الاستهلاك وتغلق
  البرنامج فعلياً. يبدأ `--hidden` مصغراً عند توفر أيقونة النظام، ويستخدم
  التشغيل التلقائي الوضع نفسه.
- **حدود أوضح.** تظهر مقابس UDP/QUIC بعبارة «السرعة غير متاحة» بدل `0 B/s`
  المضلل، وتبقى سرعات TCP ظاهرة عندما يكون للتطبيق مقابس UDP أيضاً.
- **التغطية العربية/الإنجليزية.** جميع نصوص الاستهلاك والتشخيص والتجميع
  وأيقونة النظام والتشغيل التلقائي مترجمة، مع دعم RTL.

### الحزم

- `network-monitor_1.0.5_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.5-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.5-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.0.5-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `SHA256SUMS` — بصمات أصول الإصدار
- `SHA256SUMS.asc` — توقيع GPG منفصل للبصمات

تحقق من الأصول:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### مستودع APT/RPM الموقّع

<https://asemshahen.github.io/NetworkMonitor/>

يخدم المستودع أصول الإصدار `v1.0.5` الرسمية. بصمة المفتاح:

```text
D53CB321C38875CCA82128CC77EED1C545319AE8
```

> إذا أضفت المستودع قبل 2026-10-28، فأعد استيراد المفتاح العام بالأوامر
> الموجودة في دليل التثبيت. المفتاح السابق فُقد واستُبدل بمفتاح جديد.
>
> أوامر APT وRPM موجودة في [دليل التثبيت](https://github.com/AsemShahen/NetworkMonitor/blob/main/docs/INSTALL.md).

### ملاحظات

- حزم `.deb` و`.rpm` تثبّت المساعد المميز وسياسة polkit.
- AppImage يحوي المساعد داخله، لكن الحظر يحتاج إلى `pkexec` و`python3`
  و`nftables` وcgroup v2 على النظام المضيف.
- حزم الإصدار تحوي `pyroute2`. التثبيت من المصدر يحتاج
  `python3 -m pip install pyroute2`، وبدونه يرجع البرنامج إلى `ss`.
- يُخزَّن الاستهلاك الشهري في `~/.local/share/network-monitor/usage.db`،
  ويُحسب فقط أثناء تشغيل البرنامج.
- لا توفر مقابس UDP/QUIC عدّاد بايت موثوقاً عبر sock_diag، لذلك تظهر
  غير مقيسة بدل `0 B/s`.
- تبني أصول الإصدار عبر GitHub Actions على Ubuntu 22.04، ويخدم المستودع
  الموقّع الأصول الرسمية نفسها.
- تغطي الاختبارات 23 حالة، منها تحليل `ss`، وفك خصائص Netlink، وهوية
  cgroup/AppImage، وتقسيم SQLite الشهري واليومي، وتصدير CSV، والتصفير
  والتقليم، وإعدادات التكوين، واللغتين.

## Author

**Author:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free

**Email:** <asemshahen5@gmail.com>
