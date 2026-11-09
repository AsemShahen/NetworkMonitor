# عدّة إطلاق Network Monitor

ملف داخلي للتسويق وقائمة الإطلاق. حدّث حالة القنوات بعد نشرها فعليًا؛
لا تدّعِ أن قناة أصبحت متاحة قبل ذلك.

## الحقائق

- **الاسم:** Network Monitor — مراقب الشبكة
- **المؤلف:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free
- **البريد:** <asemshahen5@gmail.com>
- **الترخيص:** GPL-3.0-or-later
- **المستودع:** <https://github.com/AsemShahen/NetworkMonitor>
- **الإصدار:** <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>
- **مستودع الحزم:** <https://asemshahen.github.io/NetworkMonitor/> (متاح؛ يخدم `v1.1.0` موقّعًا بالمفتاح الحالي)
- **بصمة GPG:** `D53CB321C38875CCA82128CC77EED1C545319AE8` (المفتاح السابق `4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE` متقاعد)
- **AUR:** `network-monitor-qt-bin` (ملفات `1.1.0` جاهزة مع بصمة `.deb` التي بناها CI؛ لا يوجد حساب AUR بعد، والتسجيل مغلق مؤقتًا بـHTTP 503)
- **GitHub Discussions:** الإعلانات مفعّلة؛ منشور 1.1.0 على <https://github.com/AsemShahen/NetworkMonitor/discussions/2>
- **AppImageHub:** PR بملف واحد <https://github.com/AppImage/appimage.github.io/pull/10786> دُمج في 2026-11-02 (نجح الاختبار على `v1.0.4`؛ إعادة اختبار `v1.1.0` معلّقة؛ عولج تحذيرا v1.0.3: الثيم الداكن افتراضيًا وغياب معلومات تحديث AppImage)
- **Show HN:** أُرسل <https://news.ycombinator.com/item?id=50268737> لكنه أصبح `[dead]`؛ لا يوجد منشور حي على Hacker News.
- **نصائح إخبارية:** أُرسلت من <asemshahen5@gmail.com> إلى `news@phoronix.com` و`contact@omgubuntu.co.uk` في 2026-11-09؛ لا يوجد رد بعد.
- **Reddit:** منشور r/linux <https://www.reddit.com/r/linux/comments/1xhdqqs/network_monitor_perapp_bandwidth_monitor_with/> أزاله AutoModerator لأن الحساب يملك 1 من الكارما؛ ومحاولة r/linuxapps اصطدمت بحد المعدل/خطأ من Reddit، لذا لا يوجد منشور Reddit حي بعد.

> الإصدار 1.1.0 هو إصدار الأمان والتهديدات. المسودات أدناه محدّثة لـ1.1.0؛
> استخدم `docs/LAUNCH_v1.1.0.md` و`docs/LAUNCH_v1.1.0_AR.md` كعدّة إطلاق
> كاملة لكل قناة.

## الوصف المختصر

Network Monitor تطبيق سطح مكتب ثنائي اللغة (إنجليزي/عربي) لينكس
(Debian/Ubuntu وFedora). يعرض سرعة التنزيل والرفع اللحظية لكل تطبيق،
والاتصالات النشطة، ومسارات الملفات التنفيذية، وإجماليات الجلسة، ورسمًا
بيانيًا تفاعليًا. يعرض الاستهلاك الشهري واليومي في تبويبي جدول ومخطط
منفصلين مع تصدير CSV. يحافظ جامع الخلفية الاختياري على تحديث الاستهلاك أثناء
إغلاق التطبيق عبر خدمة systemd للمستخدم وتنسيق SQLite بكاتب واحد. الحظر
فعلي عبر cgroup v2 وnftables من خلال مساعد محمي بـpolkit، مع قائمة حظر
دائمة واستيراد/تصدير.

يضيف الإصدار 1.1.0 تبويب **الأمان والتهديدات**. تكشف الفحوص المحلية المسارات
التنفيذية المؤقتة ومنافذ التعدين الشائعة وارتفاعات الرفع المفاجئة. وتستخدم
الفحوص الاختيارية مفاتيح API الخاصة بالمستخدم لسمعة عناوين IP عبر
AbuseIPDB/VirusTotal وبصمات الملفات عبر MalwareBazaar/VirusTotal، مع ذاكرة
SQLite محلية وحظر مؤكد لعناوين IP. الفحوص المحلية تعمل دون اتصال.

التطبيق محلي أولًا: يقرأ `/proc` ولا يحتاج حسابًا أو خدمة سحابية. الواجهة
الافتراضية إنجليزية، ويمكن تبديلها فورًا إلى العربية مع دعم RTL كامل.

## منشور Show HN

**تم الإرسال (أصبح `[dead]` الآن):** <https://news.ycombinator.com/item?id=50268737>

**العنوان:** Show HN: Network Monitor – per-app bandwidth and blocking for Linux

**النص:**

> بنيت Network Monitor لأنني أردت معرفة أي تطبيق على لينكس يستهلك الشبكة،
> وليس فقط سرعة الواجهة الإجمالية.
>
> يعرض التطبيق سرعات التنزيل والرفع اللحظية لكل عملية، والاتصالات النشطة،
> ومسارات الملفات التنفيذية، وإجماليات الجلسة، ورسمًا زمنيًا. يمكن البحث
> والفرز وإخفاء العمليات الخاملة وتصدير الأسماء. الحظر ليس وهميًا: يستخدم
> cgroup v2 وnftables عبر مساعد محمي بـpolkit، مع قائمة حظر دائمة
> واستيراد/تصدير.
>
> الواجهة إنجليزية/عربية مع RTL، والافتراضي إنجليزي. الترخيص
> GPL-3.0-or-later، ويعمل محليًا من `/proc` دون حساب أو تتبّع.
>
> الحزم: `.deb` و`.rpm` و`.AppImage` على GitHub Releases، ومستودع APT/RPM
> موقّع متاح على GitHub Pages. يسعدني تلقي ملاحظات حول التغليف
> وتوافق Fedora/RHEL ومساعد الحظر.

## Reddit

استخدم الصيغة المناسبة لكل مجتمع، ولا تنشر النص نفسه في كل الأماكن دفعة واحدة.

**محاولة في r/linux (أزالها AutoModerator: الحساب يملك 1 من الكارما):**
<https://www.reddit.com/r/linux/comments/1xhdqqs/network_monitor_perapp_bandwidth_monitor_with/>

### r/linux

**العنوان:** Network Monitor: per-app bandwidth monitor with real nftables blocking

أصدرت Network Monitor 1.1.0، تطبيق سطح مكتب GPL-3.0-or-later لينكس. يعرض
سرعات التنزيل والرفع اللحظية لكل تطبيق، والاتصالات، ومسارات الملفات
التنفيذية، وإجماليات الجلسة، والاستهلاك الشهري واليومي. يضيف الإصدار الجديد
تبويب **الأمان والتهديدات**: فحص محلي للمسارات المؤقتة ومنافذ التعدين
وارتفاعات الرفع، وفحص اختياري لسمعة عناوين IP عبر AbuseIPDB/VirusTotal
وبصمات SHA-256 عبر MalwareBazaar/VirusTotal بمفاتيح API الخاصة بك، وذاكرة
SQLite محلية، وحظر مؤكد لعناوين IP. الفحوص المحلية تعمل دون مفاتيح. يبقى
جامع الخلفية الاختياري يحدّث الاستهلاك أثناء إغلاق التطبيق عبر خدمة systemd
للمستخدم وتنسيق SQLite بكاتب واحد. يحظر التطبيقات عبر cgroup v2 + nftables
بواسطة polkit، والواجهة إنجليزية/عربية مع RTL.

الحزم: `.deb` و`.rpm` و`.AppImage`. المصدر وملاحظات الإصدار:
<https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

أبحث عن ملاحظات حول فحوص الأمان والتغليف وأي توزيعات/بيئات سطح مكتب تحتاج
اختبارًا أكبر.

### r/Ubuntu

**العنوان:** Per-app network monitor with blocking for Ubuntu (deb + signed repo)

أصدرت Network Monitor 1.1.0 لـUbuntu/Debian. يعرض سرعة كل تطبيق ويحظر
التطبيقات المحددة عبر cgroup v2 + nftables وpolkit. يضيف الإصدار الجديد
تبويب **الأمان والتهديدات** مع فحص محلي، وفحص اختياري لسمعة عناوين IP عبر
AbuseIPDB/VirusTotal، وفحص SHA-256 للملفات، وحظر مؤكد لعناوين IP. يحافظ
جامع الخلفية الاختياري على تحديث الاستهلاك أثناء إغلاق التطبيق، ويتحقق
المحدّث الداخلي من البصمات الموقّعة قبل التثبيت. توجد حزمة `.deb` على GitHub
Releases ومستودع APT موقّع على GitHub Pages.

التعليمات ومعرض اللقطات المحدّث:
<https://github.com/AsemShahen/NetworkMonitor#جولة-بصرية-في-110>

### r/Fedora

**العنوان:** Network Monitor 1.1.0 RPM: per-app bandwidth, security findings, and nftables blocking

أصدرت حزمة RPM لـFedora/RHEL لتطبيق Network Monitor، وهو مراقب استهلاك
لكل تطبيق مع حظر فعلي عبر cgroup v2 + nftables وpolkit. يضيف الإصدار 1.1.0
تبويب **الأمان والتهديدات** مع فحص محلي، وفحص اختياري لسمعة عناوين IP عبر
AbuseIPDB/VirusTotal، وفحص SHA-256 للملفات، وذاكرة SQLite محلية، وحظر مؤكد
لعناوين IP. الواجهة إنجليزية/عربية مع RTL، ويحافظ جامع الخلفية الاختياري على
تحديث الاستهلاك أثناء إغلاق التطبيق، ويتحقق المحدّث الداخلي من البصمات
الموقّعة قبل التثبيت. حزمة مصدر مراجعة Fedora مرفقة بالإصدار للخطأ `2568606`.

RPM: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>
حزمة المصدر: <https://github.com/AsemShahen/NetworkMonitor/releases/download/v1.1.0/network-monitor-1.1.0-1.fc45.src.rpm>
مستودع RPM موقّع: <https://asemshahen.github.io/NetworkMonitor/>

أرحّب بملاحظات حول تغليف Fedora وسلوك SELinux/nftables.

### r/archlinux

**العنوان:** network-monitor-qt-bin: per-app bandwidth monitor with blocking

جهّزت حزمة AUR باسم `network-monitor-qt-bin` لتطبيق Network Monitor. تفك
ملف `.deb` الرسمي وتثبّت التطبيق والمساعد وسياسة polkit والأيقونات وملف
سطح المكتب.

المصدر: <https://github.com/AsemShahen/NetworkMonitor>
AUR: `yay -S network-monitor-qt-bin` (بعد القبول)

الاسم مختلف عن `network-monitor-bin` الموجود، لأنه يخص مشروعًا آخر.

### المجتمعات العربية

**العنوان:** مراقب الشبكة: راقب استهلاك كل تطبيق واحظره على لينكس

أصدرت Network Monitor 1.1.0، تطبيقًا مفتوح المصدر (GPL-3.0-or-later)
لمراقبة سرعة التنزيل والرفع لكل تطبيق على لينكس، مع حظر فعلي عبر cgroup v2
وnftables ومصادقة polkit. يضيف الإصدار الجديد تبويب **الأمان والتهديدات**:
فحص محلي للمسارات المؤقتة ومنافذ التعدين وارتفاعات الرفع، وفحص اختياري لسمعة
عناوين IP عبر AbuseIPDB/VirusTotal وبصمات SHA-256 عبر MalwareBazaar/VirusTotal
بمفاتيح API الخاصة بك، وذاكرة SQLite محلية، وحظر مؤكد لعناوين IP. الواجهة
إنجليزية وعربية مع دعم كامل للاتجاه من اليمين إلى اليسار، والافتراضي إنجليزي.

الحزم: `.deb` و`.rpm` و`.AppImage`، ومستودع APT/RPM موقّع.
المصدر والتنزيل:
<https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

يسعدني اختباركم على توزيعاتكم، خصوصًا Fedora وArch وopenSUSE.

## اقتراحات لمواقع أخبار لينكس

أرسل ملاحظة قصيرة مع رابط ولقطة شاشة إلى:

- Phoronix: <https://www.phoronix.com/contact>
- OMG! Ubuntu: <https://www.omgubuntu.co.uk/contact>
- It's FOSS: <https://itsfoss.com/contact/>
- Linux Uprising: <https://www.linuxuprising.com/p/contact.html>
- Fedora Magazine: <https://fedoramagazine.org/contribute/>
- Ubuntu Discourse: <https://discourse.ubuntu.com/>

**الموضوع المقترح:** `Network Monitor 1.1.0: per-app bandwidth, security findings, and nftables blocking for Linux`

**النص المقترح:**

> Network Monitor 1.1.0 تطبيق سطح مكتب GPL-3.0-or-later لينكس يعرض سرعة
> التنزيل والرفع اللحظية لكل تطبيق، ويحظر التطبيقات المحددة عبر cgroup v2 +
> nftables من خلال مساعد polkit. يضيف تبويب الأمان والتهديدات فحصًا محليًا
> للمسارات المؤقتة ومنافذ التعدين وارتفاعات الرفع، وفحصًا اختياريًا لسمعة
> عناوين IP عبر AbuseIPDB/VirusTotal وSHA-256 للملفات عبر
> MalwareBazaar/VirusTotal، وذاكرة SQLite محلية، وحظرًا مؤكدًا لعناوين IP.
> يحافظ جامع الخلفية الاختياري على تحديث الاستهلاك أثناء إغلاق التطبيق.
> يتوفر كـ`.deb` و`.rpm` و`.AppImage`، وله مستودع APT/RPM موقّع وواجهة
> إنجليزية/عربية مع RTL. لقطات الشاشة وملاحظات الإصدار:
> <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

## SEO

**العنوان:** Network Monitor — مراقب استهلاك الإنترنت لكل تطبيق على لينكس

**الوصف:** شاهد سرعة التنزيل والرفع اللحظية لكل تطبيق على لينكس، وافحص
الاتصالات، واحظر التطبيقات عبر cgroup v2 + nftables. واجهة إنجليزية/عربية،
حزم deb/rpm/AppImage، وترخيص GPL-3.0-or-later.

**الكلمات:** مراقب شبكة لينكس، مراقب استهلاك لكل تطبيق، استهلاك الشبكة لكل
عملية، حظر التطبيقات nftables، cgroup v2، تطبيق لينكس عربي، دعم RTL،
مراقب شبكة Ubuntu، مراقب شبكة Fedora، AppImage، مفتوح المصدر.

استخدم في وصف GitHub والمواضيع:

`linux`, `network-monitor`, `bandwidth-monitor`, `nftables`, `cgroup-v2`,
`pyside6`, `qt6`, `arabic`, `rtl`, `appimage`, `debian`, `fedora`, `gpl-3-0`.

## فيديو تجريبي (30–45 ثانية)

1. افتح تبويب Live وأظهر تطبيقين أو ثلاثة بسرعات متغيرة.
2. انتقل إلى Chart واترك الرسم يتحرك.
3. ابحث عن تطبيق، حدده، واضغط **Block selected**.
4. وثّق polkit، ثم أظهر التطبيق في **Blocked apps**.
5. افتح **Settings → Language** وبدّل إلى العربية؛ أظهر واجهة RTL.
6. اختم ببطاقة About التي تعرض المؤلف والبريد، ثم رابط الإصدار.

سجّل بدقة 1366×738 أو 1920×1080، 30 إطارًا/ثانية، دون إشعارات. استخدم
لقطات `docs/screenshots/` كصور مصغّرة.

## قائمة الإطلاق

- [x] دفع فرع `gh-pages` وتفعيل Pages.
- [x] عودة <https://asemshahen.github.io/NetworkMonitor/> بشكل صحيح.
- [x] التحقق من `apt/dists/stable/InRelease` بالمفتاح المنشور.
- [x] التحقق من `rpm/x86_64/repodata/repomd.xml.asc` بالمفتاح المنشور.
- [ ] دفع حزمة AUR `network-monitor-qt-bin` وظهورها (متوقف: لا يوجد حساب AUR بعد، والتسجيل مغلق مؤقتًا، HTTP 503).
- [x] فتح PR في AppImageHub (ملف واحد فقط)، ونجح الاختبار، ودُمج في 2026-11-02.
- [x] نجاح اختبار AppImageHub على `v1.0.4` (v1.0.1 بلا `libxkbcommon-x11`؛ v1.0.2 بمرجع glibc 2.38؛ v1.0.3 مبني على Ubuntu 22.04؛ v1.0.4 يعالج الثيم الداكن الافتراضي ويضيف معلومات تحديث `.zsync`).
- [ ] إعادة اختبار AppImage الخاص بـ`v1.1.0` على AppImageHub بعد تغييرات الأمان والتهديدات واللقطات.
- [x] ظهور لقطات README على GitHub.
- [x] ذكر المستودع الموقّع وحالة AUR وAppImageHub في ملاحظات الإصدار.
- [x] نشر Show HN: <https://news.ycombinator.com/item?id=50268737>
- [x] محاولة r/linux: <https://www.reddit.com/r/linux/comments/1xhdqqs/network_monitor_perapp_bandwidth_monitor_with/> (أزالها AutoModerator؛ الحساب يملك 1 من الكارما)
- [ ] نشر أحد المجتمعات: محاولة r/linuxapps اصطدمت بحد المعدل/خطأ من Reddit؛ انتظر أو ابنِ تاريخًا للحساب.
- [ ] الانتظار قبل النشر المتعدد.
- [ ] إرسال ثلاث ملاحظات لمواقع أخبار لينكس مع لقطة شاشة.
- [x] إضافة رابط المستودع إلى حقل Homepage في GitHub.
