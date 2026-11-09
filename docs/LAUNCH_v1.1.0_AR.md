# عدّة إطلاق Network Monitor 1.1.0

مسودات جاهزة للنشر في مجتمعات لينكس. انشر في مجتمع واحد في كل مرة، واذكر أنك
المؤلف، وردّ على الأسئلة، ولا تنشر النص نفسه في كل الأماكن في اليوم نفسه.

## الحقائق

- **الإصدار:** <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>
- **المستودع:** <https://github.com/AsemShahen/NetworkMonitor>
- **الترخيص:** GPL-3.0-or-later
- **المؤلف:** AL-Asem Software By Asem Shahen
- **التبويب الجديد:** **الأمان والتهديدات** / **Security & Threats**
- **الحزم:** `.deb` و`.rpm` وAppImage وأرشيف `/opt` اليدوي
- **المستودع الموقّع:** <https://asemshahen.github.io/NetworkMonitor/>
- **لقطة الشاشة:** <https://raw.githubusercontent.com/AsemShahen/NetworkMonitor/main/docs/screenshots/security.png>

## وصف مختصر

Network Monitor تطبيق سطح مكتب ثنائي اللغة (إنجليزي/عربي) لينكس
(Debian/Ubuntu وFedora). يعرض سرعة التنزيل والرفع اللحظية لكل تطبيق عبر
عدّادات Netlink الأصلية، مع رجوع إلى `ss` و`/proc/net`. ويعرض الاتصالات
النشطة ومسارات الملفات التنفيذية وإجماليات الجلسة والاستهلاك الشهري واليومي
ورسمًا بيانيًا تفاعليًا. الحظر فعلي عبر cgroup v2 وnftables من خلال مساعد
محمي بـpolkit، مع قائمة حظر دائمة واستيراد/تصدير.

يضيف الإصدار 1.1.0 تبويب **الأمان والتهديدات**: يكشف محليًا الملفات التنفيذية
التي تعمل من مسارات مؤقتة، والاتصالات بمنافذ تعدين شائعة، وارتفاعات الرفع
المفاجئة. ويمكن اختياريًا، باستخدام مفاتيح API الخاصة بك، فحص عناوين IP عبر
AbuseIPDB/VirusTotal وبصمات الملفات عبر MalwareBazaar/VirusTotal. تُخزّن
النتائج في SQLite محلي، ويمكن حظر عناوين IP بعد التأكيد.

التطبيق محلي أولًا: الفحوص المحلية لا تحتاج حسابًا أو خدمة سحابية. الواجهة
الافتراضية إنجليزية وتبدّل فورًا إلى العربية مع دعم RTL كامل.

## Show HN

**العنوان:** Show HN: Network Monitor – per-app bandwidth and a new security tab for Linux

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
> يضيف الإصدار 1.1.0 تبويب الأمان والتهديدات. يكشف المحلي الملفات التنفيذية
> التي تعمل من مسارات مؤقتة، والاتصالات بمنافذ تعدين شائعة، وارتفاعات الرفع.
> وإذا أضفت مفاتيح API الخاصة بك، يمكنه فحص عناوين IP عبر
> AbuseIPDB/VirusTotal وبصمات الملفات عبر MalwareBazaar/VirusTotal. تُخزّن
> النتائج محليًا في SQLite، ويمكن حظر عناوين IP بعد التأكيد. الفحوص المحلية
> تعمل دون اتصال، ولا يوجد تتبّع.
>
> الواجهة إنجليزية/عربية مع RTL، والافتراضي إنجليزي. الترخيص
> GPL-3.0-or-later، ويعمل محليًا من `/proc`.
>
> الحزم: `.deb` و`.rpm` و`.AppImage` على GitHub Releases، ومستودع APT/RPM
> موقّع متاح على GitHub Pages. يسعدني تلقي ملاحظات حول فحوص الأمان والتغليف
> وتوافق Fedora/RHEL ومساعد الحظر.

## Reddit

استخدم الصيغة المناسبة لكل مجتمع، واذكر أنك المؤلف، ولا تنشر النص نفسه في كل
الأماكن دفعة واحدة.

### r/linux

**العنوان:** Network Monitor 1.1.0: per-app bandwidth monitor with a new security tab

أصدرت Network Monitor 1.1.0، تطبيق سطح مكتب GPL-3.0-or-later لينكس. يعرض
سرعات التنزيل والرفع اللحظية لكل تطبيق عبر Netlink، والاتصالات، ومسارات
الملفات التنفيذية، وإجماليات الجلسة، والاستهلاك الشهري واليومي. ويحظر
التطبيقات عبر cgroup v2 + nftables بواسطة polkit، والواجهة إنجليزية/عربية مع
RTL.

يضيف الإصدار الجديد تبويب الأمان والتهديدات: فحص محلي للمسارات المؤقتة
ومنافذ التعدين وارتفاعات الرفع، وفحص اختياري لسمعة عناوين IP عبر
AbuseIPDB/VirusTotal، وفحص SHA-256 للملفات عبر MalwareBazaar/VirusTotal،
وذاكرة SQLite محلية، وحظر مؤكد لعناوين IP. الفحوص المحلية تعمل دون مفاتيح
API.

الحزم: `.deb` و`.rpm` و`.AppImage`.
المصدر وملاحظات الإصدار:
<https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

أبحث عن ملاحظات حول فحوص الأمان والتغليف وأي توزيعات/بيئات سطح مكتب تحتاج
اختبارًا أكبر.

### r/linuxapps

**العنوان:** Network Monitor 1.1.0 – per-app bandwidth, security findings, and nftables blocking

Network Monitor تطبيق لينكس محلي أولًا لمراقبة استهلاك الشبكة لكل تطبيق.
يضيف الإصدار 1.1.0 تبويب الأمان والتهديدات مع فحص محلي، وفحص اختياري لسمعة
عناوين IP وبصمات الملفات، وحظر مؤكد لعناوين IP. يستخدم المراقب الرئيسي
عدّادات Netlink ويحفظ الاستهلاك الشهري واليومي ويدعم محدّثًا موقّعًا لحزم
GitHub.

الواجهة إنجليزية/عربية مع RTL، والترخيص GPL-3.0-or-later. لقطة الشاشة
والتنزيل: <https://github.com/AsemShahen/NetworkMonitor>

### r/Ubuntu

**العنوان:** Network Monitor 1.1.0 for Ubuntu: per-app bandwidth + security tab (deb)

أصدرت Network Monitor 1.1.0 لـUbuntu/Debian. يعرض سرعة كل تطبيق بدقة عبر
Netlink، ويحفظ الاستهلاك الشهري واليومي، ويضيف تبويب الأمان والتهديدات مع فحص
محلي وفحص اختياري للسمعة وحظر مؤكد لعناوين IP عبر nftables.

توجد حزمة `.deb` على GitHub Releases ومستودع APT موقّع على GitHub Pages.
التعليمات ولقطات الشاشة:
<https://github.com/AsemShahen/NetworkMonitor>

### r/Fedora

**العنوان:** Network Monitor 1.1.0 RPM: per-app bandwidth + security findings

أصدرت حزمة RPM لـFedora/RHEL لتطبيق Network Monitor 1.1.0، وهو مراقب استهلاك
لكل تطبيق مع حظر فعلي عبر cgroup v2 + nftables وpolkit. يضيف تبويب الأمان
والتهديدات فحصًا محليًا وفحصًا اختياريًا للسمعة وحظرًا مؤكدًا لعناوين IP.
الواجهة إنجليزية/عربية مع RTL، ويتحقق المحدّث الداخلي من البصمات الموقّعة.

RPM: <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>
مستودع RPM موقّع: <https://asemshahen.github.io/NetworkMonitor/>

أرحّب بملاحظات حول تغليف Fedora وسلوك SELinux/nftables.

### r/archlinux

**العنوان:** network-monitor-qt-bin 1.1.0: per-app bandwidth monitor with security tab

حدّثت حزمة AUR باسم `network-monitor-qt-bin` لتطبيق Network Monitor 1.1.0.
تفك ملف `.deb` الرسمي وتثبّت التطبيق والمساعد وسياسة polkit والأيقونات وملف
سطح المكتب. يضيف الإصدار الجديد تبويب الأمان والتهديدات مع فحص محلي وفحص
اختياري للسمعة وحظر مؤكد لعناوين IP.

المصدر: <https://github.com/AsemShahen/NetworkMonitor>
AUR: `yay -S network-monitor-qt-bin` (بعد القبول)

الاسم مختلف عن `network-monitor-bin` الموجود، لأنه يخص مشروعًا آخر.

### المجتمعات العربية

**العنوان:** مراقب الشبكة 1.1.0: راقب استهلاك كل تطبيق واحظره على لينكس

أصدرت Network Monitor 1.1.0، تطبيقًا مفتوح المصدر (GPL-3.0-or-later)
لمراقبة سرعة التنزيل والرفع لكل تطبيق على لينكس، مع حظر فعلي عبر cgroup v2
وnftables ومصادقة polkit. يضيف الإصدار الجديد تبويب **الأمان والتهديدات**:
فحص محلي للمسارات المؤقتة ومنافذ التعدين وارتفاعات الرفع، وفحص اختياري لسمعة
عناوين IP وبصمات الملفات باستخدام مفاتيح API الخاصة بك، وذاكرة SQLite محلية،
وحظر مؤكد لعناوين IP.

الواجهة إنجليزية وعربية مع دعم RTL كامل، والافتراضي إنجليزي. الحزم: `.deb`
و`.rpm` و`.AppImage`، ومستودع APT/RPM موقّع.
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

**الموضوع المقترح:** `Network Monitor 1.1.0: per-app bandwidth + security findings for Linux`

**النص المقترح:**

> Network Monitor 1.1.0 تطبيق سطح مكتب GPL-3.0-or-later لينكس يعرض سرعة
> التنزيل والرفع اللحظية لكل تطبيق عبر عدّادات Netlink، ويحفظ الاستهلاك
> الشهري واليومي، ويحظر التطبيقات المحددة عبر cgroup v2 + nftables من خلال
> مساعد polkit. يضيف تبويب الأمان والتهديدات فحصًا محليًا للمسارات المؤقتة
> ومنافذ التعدين وارتفاعات الرفع، وفحصًا اختياريًا لسمعة عناوين IP عبر
> AbuseIPDB/VirusTotal وSHA-256 للملفات عبر MalwareBazaar/VirusTotal، وذاكرة
> SQLite محلية، وحظرًا مؤكدًا لعناوين IP. يتوفر كـ`.deb` و`.rpm` و`.AppImage`،
> وله مستودع APT/RPM موقّع وواجهة إنجليزية/عربية مع RTL. لقطات الشاشة
> وملاحظات الإصدار:
> <https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

## منشورات المنتديات

### Fedora Discussion

**العنوان:** Network Monitor 1.1.0 RPM – feedback on nftables/SELinux behavior

Network Monitor مراقب استهلاك لكل تطبيق مع حظر فعلي عبر cgroup v2 + nftables
وpolkit. ملف Fedora في شجرة المصدر وطلب المراجعة هو خطأ Fedora `2568606`.
يضيف الإصدار 1.1.0 تبويب الأمان والتهديدات مع فحص محلي وفحص اختياري للسمعة.
أبحث عن ملاحظات حول RPM وقواعد nftables وسلوك SELinux. RPM وملاحظات الإصدار:
<https://github.com/AsemShahen/NetworkMonitor/releases/tag/v1.1.0>

### منتديات Debian / قائمة مستخدمي Debian

**الموضوع:** Network Monitor 1.1.0 – per-app bandwidth and security tab

Network Monitor تطبيق Qt/PySide6 مفتوح المصدر (GPL-3.0-or-later) لـDebian
وUbuntu. يعرض استهلاك كل تطبيق عبر Netlink، ويحفظ الاستهلاك الشهري، ويحظر
التطبيقات عبر cgroup v2 + nftables بواسطة polkit. يضيف الإصدار 1.1.0 تبويب
الأمان والتهديدات مع فحص محلي وفحص اختياري للسمعة. حزمة المصدر جاهزة لـDebian
وطلب RFS هو خطأ Debian `1153391`. أرحب بملاحظات حول الحزمة والتبويب:
<https://github.com/AsemShahen/NetworkMonitor>

### Ubuntu Discourse

**العنوان:** Network Monitor 1.1.0 – per-app bandwidth and a security tab for Ubuntu

Network Monitor متاح كـ`.deb` وعبر مستودع APT موقّع. يضيف الإصدار 1.1.0 تبويب
الأمان والتهديدات مع فحص محلي، وفحص اختياري عبر AbuseIPDB/VirusTotal، وفحص
SHA-256 للملفات، وحظر مؤكد لعناوين IP عبر nftables. ويعرض التطبيق أيضًا
السرعات اللحظية لكل تطبيق والاستهلاك الشهري والتطبيقات المحظورة. لقطات
الشاشة وتعليمات التثبيت:
<https://github.com/AsemShahen/NetworkMonitor>

## قائمة الإطلاق

- [ ] نشر إصدار GitHub والتحقق من كل الأصول.
- [ ] تحديث مستودع APT/RPM الموقّع وبيانات AUR.
- [ ] نشر تحديث في مجتمع واحد، ثم الانتظار للتعليقات.
- [ ] إرسال ملاحظتين أو ثلاث لمواقع أخبار لينكس مع لقطة الأمان.
- [ ] الرد على الأسئلة وفرز تقارير الأخطاء.
- [ ] لا تدّعِ نشر Debian/Fedora الرسمي قبل قبول الراعي/المراجع.
- [ ] لا تنشئ حسابات منتديات تلقائيًا؛ استخدم حسابات المؤلف واتبع قواعد كل
      مجتمع.

## ملاحظات

- أزال AutoModerator منشور r/linux السابق لأن الحساب يملك 1 من الكارما. ابنِ
  تاريخًا للحساب قبل إعادة المحاولة، أو اسأل مشرفًا.
- منشور Show HN الحالي هو
  <https://news.ycombinator.com/item?id=50268737>؛ لا تنشر Show HN جديدًا إلا
  إذا كان الإصدار جديدًا فعليًا وكانت قواعد المجتمع تسمح.
- النص الإنجليزي متاح أيضًا في `docs/LAUNCH_v1.1.0.md`.
