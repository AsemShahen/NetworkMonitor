# عدّة إطلاق Network Monitor

ملف داخلي للتسويق وقائمة الإطلاق. حدّث حالة القنوات بعد نشرها فعليًا؛
لا تدّعِ أن قناة أصبحت متاحة قبل ذلك.

## الحقائق

- **الاسم:** Network Monitor — مراقب الشبكة
- **المؤلف:** AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free
- **البريد:** <asemshahen5@gmail.com>
- **الترخيص:** GPL-3.0-or-later
- **المستودع:** <https://github.com/AsemShahen/NetworkMonitor>
- **الإصدار:** <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.3>
- **مستودع الحزم:** <https://asemshahen.github.io/NetworkMonitor/> (متاح؛ يخدم حاليًا أصول `v1.0.1` الرسمية)
- **بصمة GPG:** `4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`
- **AUR:** `network-monitor-qt-bin` (حزمة `1.0.3` المحلية جاهزة؛ بانتظار مفتاح حساب AUR والدفع)
- **AppImageHub:** PR بملف واحد <https://github.com/AppImage/appimage.github.io/pull/10786> (نجح الاختبار على `v1.0.3`؛ تحذيران: الثيم الداكن افتراضيًا ولا معلومات تحديث لـAppImage)

## الوصف المختصر

Network Monitor تطبيق سطح مكتب داكن ثنائي اللغة (إنجليزي/عربي) لينكس
(Debian/Ubuntu وFedora). يعرض سرعة التنزيل والرفع اللحظية لكل تطبيق،
والاتصالات النشطة، ومسارات الملفات التنفيذية، وإجماليات الجلسة، ورسمًا
بيانيًا تفاعليًا. الحظر فعلي عبر cgroup v2 وnftables من خلال مساعد محمي
بـpolkit، مع قائمة حظر دائمة واستيراد/تصدير.

التطبيق محلي أولًا: يقرأ `/proc` ولا يحتاج حسابًا أو خدمة سحابية. الواجهة
الافتراضية إنجليزية، ويمكن تبديلها فورًا إلى العربية مع دعم RTL كامل.

## منشور Show HN

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

### r/linux

**العنوان:** Network Monitor: per-app bandwidth monitor with real nftables blocking

أصدرت Network Monitor 1.0.3، تطبيق سطح مكتب GPL-3.0-or-later لينكس. يعرض
سرعات التنزيل والرفع اللحظية لكل تطبيق، والاتصالات، ومسارات الملفات
التنفيذية، وإجماليات الجلسة، ورسمًا بيانيًا. يحظر التطبيقات عبر cgroup v2 +
nftables بواسطة polkit، والواجهة إنجليزية/عربية مع RTL.

الحزم: `.deb` و`.rpm` و`.AppImage`. المصدر:
<https://github.com/AsemShahen/NetworkMonitor>

أبحث عن ملاحظات حول التغليف وأي توزيعات/بيئات سطح مكتب تحتاج اختبارًا أكبر.

### r/Ubuntu

**العنوان:** Per-app network monitor with blocking for Ubuntu (deb + signed repo)

أصدرت Network Monitor 1.0.3 لـUbuntu/Debian. يعرض سرعة كل تطبيق ويحظر
التطبيقات المحددة عبر cgroup v2 + nftables وpolkit. توجد حزمة `.deb` على
GitHub Releases ومستودع APT موقّع على GitHub Pages.

التعليمات ولقطات الشاشة:
<https://github.com/AsemShahen/NetworkMonitor>

### r/Fedora

**العنوان:** Network Monitor 1.0.3 RPM: per-app bandwidth and nftables blocking

أصدرت حزمة RPM لـFedora/RHEL لتطبيق Network Monitor، وهو مراقب استهلاك
لكل تطبيق مع حظر فعلي عبر cgroup v2 + nftables وpolkit. الواجهة
إنجليزية/عربية مع RTL.

RPM: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.3>
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

أصدرت Network Monitor 1.0.3، تطبيقًا مفتوح المصدر (GPL-3.0-or-later)
لمراقبة سرعة التنزيل والرفع لكل تطبيق على لينكس، مع حظر فعلي عبر cgroup v2
وnftables ومصادقة polkit. الواجهة إنجليزية وعربية مع دعم كامل للاتجاه من
اليمين إلى اليسار، والافتراضي إنجليزي.

الحزم: `.deb` و`.rpm` و`.AppImage`، ومستودع APT/RPM موقّع.
المصدر والتنزيل: <https://github.com/AsemShahen/NetworkMonitor>

يسعدني اختباركم على توزيعاتكم، خصوصًا Fedora وArch وopenSUSE.

## اقتراحات لمواقع أخبار لينكس

أرسل ملاحظة قصيرة مع رابط ولقطة شاشة إلى:

- Phoronix: <https://www.phoronix.com/contact>
- OMG! Ubuntu: <https://www.omgubuntu.co.uk/contact>
- It's FOSS: <https://itsfoss.com/contact/>
- Linux Uprising: <https://www.linuxuprising.com/p/contact.html>
- Fedora Magazine: <https://fedoramagazine.org/contribute/>
- Ubuntu Discourse: <https://discourse.ubuntu.com/>

**الموضوع المقترح:** `Network Monitor 1.0.3: per-app bandwidth + nftables blocking for Linux`

**النص المقترح:**

> Network Monitor 1.0.3 تطبيق سطح مكتب GPL-3.0-or-later لينكس يعرض سرعة
> التنزيل والرفع اللحظية لكل تطبيق، ويحظر التطبيقات المحددة عبر cgroup v2 +
> nftables من خلال مساعد polkit. يتوفر كـ`.deb` و`.rpm` و`.AppImage`، وله
> مستودع APT/RPM موقّع وواجهة إنجليزية/عربية مع RTL. لقطات الشاشة وملاحظات
> الإصدار: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.0.3>

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
- [ ] دفع حزمة AUR `network-monitor-qt-bin` وظهورها.
- [x] فتح PR في AppImageHub (ملف واحد فقط) ومتابعة تعليق الاختبار.
- [x] نجاح اختبار AppImageHub على `v1.0.3` (v1.0.1 بلا `libxkbcommon-x11`؛ v1.0.2 بمرجع glibc 2.38؛ v1.0.3 مبني على Ubuntu 22.04).
- [x] ظهور لقطات README على GitHub.
- [x] ذكر المستودع الموقّع وحالة AUR وAppImageHub في ملاحظات الإصدار.
- [ ] نشر Show HN وأحد المجتمعات، ثم الانتظار قبل النشر المتعدد.
- [ ] إرسال ثلاث ملاحظات لمواقع أخبار لينكس مع لقطة شاشة.
- [x] إضافة رابط المستودع إلى حقل Homepage في GitHub.
