# Network Monitor 1.0.8

Network Monitor 1.0.8 reorganizes the **Usage** tab so the daily chart and the
application table no longer compete for the same vertical space. The table and
chart now have their own inner tabs, while the monthly summary cards remain
visible above them.

## Highlights

- **Separate Usage table and chart tabs.** The first inner tab is the table and
  the second is the chart. On short windows the chart can no longer overlap the
  table or push rows out of view.
- **Summary cards stay fixed.** The monthly download, upload, and total cards
  remain above both tabs, so the selected month stays visible while switching
  views.
- **Search stays with the table.** The search field, sortable columns, filtering,
  and CSV export remain in the **Table** tab.
- **The chart gets its own space.** The **Chart** tab shows the daily download
  and upload series with the existing interactive pan and zoom controls.
- **Bilingual and RTL.** New tab labels and the chart hint are translated into
  English and Arabic, with the same RTL alignment and light/dark styling as the
  rest of the application.
- **No data or service changes.** The usage database schema, background collector,
  blocking, signed updater, and repository behavior are unchanged.

## Layout details

The Usage tab now contains a nested tab widget:

1. **Table** — search field, application table, sorting, and the existing
   monthly totals.
2. **Chart** — the daily download/upload chart.

The monthly summary cards are outside the inner tab widget, so they remain
visible in both views. The selected month dropdown still controls both tabs.
The previous behavior, where the chart and table were stacked in one layout,
caused the chart to overlap the table when the available height was too small.

## Updating

Version 1.0.6 and later can install 1.0.8 with **Settings → Application
updates → Check for updates**. The updater verifies `SHA256SUMS` and
`SHA256SUMS.asc` before installing.

For a manual `/opt/network-monitor` install from 1.0.5 or older, install once:

```bash
tar -xzf NetworkMonitor-1.0.8-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

After that, later releases can be installed from the update button.

## Assets

- `network-monitor_1.0.8_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.8-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.8-x86_64.AppImage` — portable
- `NetworkMonitor-1.0.8-x86_64.AppImage.zsync` — AppImageUpdate metadata
- `NetworkMonitor-1.0.8-linux-x86_64.tar.gz` — manual `/opt` updater archive
- `SHA256SUMS` — release file checksums
- `SHA256SUMS.asc` — detached GPG signature for the checksums

Download: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.8>

Verify the download:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

## Notes

- The table remains the default inner tab when the Usage tab is opened.
- The chart is still interactive: drag to pan and scroll to zoom.
- Usage is counted while Network Monitor or the optional background collector is
  running. See the 1.0.7 notes for background collection details.
- No telemetry, account information, or application list is sent anywhere.

## العربية

يعيد Network Monitor 1.0.8 تنظيم تبويب **الاستهلاك** بحيث لا يتنافس المخطط
اليومي وجدول التطبيقات على المساحة الرأسية نفسها. أصبح للجدول والمخطط تبويبان
داخليان منفصلان، مع بقاء بطاقات الملخص الشهرية ظاهرة أعلىهما.

### أبرز الميزات

- **تبويبان منفصلان للجدول والمخطط.** التبويب الداخلي الأول هو الجدول والثاني
  هو المخطط. في النوافذ القصيرة لم يعد المخطط يتداخل مع الجدول أو يدفع الصفوف
  خارج العرض.
- **بقاء بطاقات الملخص ثابتة.** تبقى بطاقات التنزيل والرفع والإجمالي الشهرية
  أعلى التبويبين، لذلك يظل الشهر المحدد ظاهراً أثناء تبديل العرض.
- **البحث مع الجدول.** يبقى حقل البحث والفرز والتصفية وتصدير CSV في تبويب
  **الجدول**.
- **مساحة مخصصة للمخطط.** يعرض تبويب **المخطط البياني** سلسلتي التنزيل والرفع
  اليوميتين مع أدوات التحريك والتكبير التفاعلية الحالية.
- **ثنائي اللغة ودعم RTL.** تُرجمت تسميات التبويبات وملاحظة المخطط إلى
  الإنجليزية والعربية، مع محاذاة RTL وتنسيق الوضعين الفاتح والداكن نفسهما
  المستخدمين في بقية التطبيق.
- **لا تغيير في البيانات أو الخدمات.** لم يتغير مخطط قاعدة بيانات الاستهلاك أو
  جامع الخلفية أو الحظر أو المحدّث الموقّع أو سلوك المستودع.

### تفاصيل التخطيط

يحتوي تبويب الاستهلاك الآن على أداة تبويب داخلية:

1. **الجدول** — حقل البحث وجدول التطبيقات والفرز وإجماليات الشهر الحالية.
2. **المخطط البياني** — رسم التنزيل والرفع اليومي.

تقع بطاقات الملخص الشهرية خارج أداة التبويب الداخلية، لذلك تبقى ظاهرة في
العرضين. ولا يزال منتقي الشهر يتحكم في التبويبين. كان السلوك السابق، حيث كان
المخطط والجدول متراكبين في تخطيط واحد، يسبب تداخل المخطط مع الجدول عندما تكون
المساحة الرأسية غير كافية.

### التحديث

يمكن للإصدار 1.0.6 وما بعده تثبيت 1.0.8 من
**الإعدادات ← تحديثات التطبيق ← التحقق من التحديثات**. يتحقق المحدّث من
`SHA256SUMS` و`SHA256SUMS.asc` قبل التثبيت.

إذا كان لديك تثبيت يدوي في `/opt/network-monitor` من 1.0.5 أو أقدم، فثبّت مرة
واحدة:

```bash
tar -xzf NetworkMonitor-1.0.8-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

بعد ذلك يمكن تثبيت الإصدارات اللاحقة من زر التحديث.

### الحزم

- `network-monitor_1.0.8_amd64.deb` — Debian/Ubuntu
- `network-monitor-1.0.8-1.x86_64.rpm` — Fedora/RHEL
- `NetworkMonitor-1.0.8-x86_64.AppImage` — محمولة
- `NetworkMonitor-1.0.8-x86_64.AppImage.zsync` — بيانات تحديث AppImage
- `NetworkMonitor-1.0.8-linux-x86_64.tar.gz` — أرشيف التحديث اليدوي في `/opt`
- `SHA256SUMS` — بصمات ملفات الإصدار
- `SHA256SUMS.asc` — توقيع GPG منفصل للبصمات

التحميل: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.8>

تحقق من الملفات:

```bash
gpg --verify SHA256SUMS.asc SHA256SUMS
sha256sum -c SHA256SUMS
```

### ملاحظات

- يبقى الجدول التبويب الداخلي الافتراضي عند فتح تبويب الاستهلاك.
- يبقى المخطط تفاعلياً: اسحب للتحريك ومرّر للتكبير.
- يُحسب الاستهلاك أثناء تشغيل Network Monitor أو جامع الخلفية الاختياري. راجع
  ملاحظات 1.0.7 لتفاصيل الجمع في الخلفية.
- لا تُرسل أي بيانات تتبع أو معلومات حساب أو قائمة تطبيقات إلى أي جهة.
