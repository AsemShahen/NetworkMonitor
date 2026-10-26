# بناء حزم النشر

هذه الحزم مخصّصة للنشر عبر **GitHub Releases**، وليست حزم Flatpak. تحتفظ الحزم
بالوظائف الكاملة: المراقبة لكل تطبيق، والحظر عبر cgroup v2 وnftables وpolkit.

## المخرجات

- `network-monitor_<version>_amd64.deb` — لدبيان/أوبونتو.
- `network-monitor-<version>-1.x86_64.rpm` — لفيدورا/RHEL.
- `NetworkMonitor-<version>-x86_64.AppImage` — حزمة محمولة.
- `SHA256SUMS` — بصمات الملفات.

## البناء محليًا

يتطلب البناء اتصالًا بالإنترنت في أول مرة فقط، لتنزيل Python المحمول وحزم
PySide6/pyqtgraph/numpy. بعد ذلك يمكن إعادة استخدام `build/runtime`.

```bash
./packaging/build-runtime.sh
./packaging/build-deb.sh
./packaging/build-rpm.sh
./packaging/build-appimage.sh
```

الأدوات المطلوبة:

- `dpkg-deb` لبناء deb.
- `rpmbuild` لبناء rpm.
- `curl` و`tar`.
- `desktop-file-utils` (اختياري لكنه مفيد لفحص ملف سطح المكتب).

## النشر على GitHub Releases

1. أنشئ مستودعًا عامًا باسم `NetworkMonitor` تحت الحساب `AsemShahen`.
2. ارفع المشروع والوسم:

```bash
git push -u origin main
git push origin v1.0.1
```

الوسم `v1.0.0` موجود محليًا ويشير إلى التزام الإصدار المنشور. بعد تغييرات
التغليف الحالية، أنشئ وسمًا جديدًا مثل `v1.0.1` بدل إعادة استخدام وسم منشور.

سيعمل سير العمل `.github/workflows/release.yml` تلقائيًا، ويبني الحزم الثلاث،
وينشئ Release ويحمّل الملفات إليه. يمكن أيضًا تشغيله يدويًا من تبويب Actions
لبناء الحزم ورفعها كـArtifacts فقط؛ لإنشاء Release جديد استخدم وسمًا مثل
`v1.0.1`.

## مستودع APT/RPM الموقّع

بعد إعداد مفتاح GPG وأسرار GitHub، ينشر المشروع مستودعًا موقّعًا على
GitHub Pages:

<https://asemshahen.github.io/NetworkMonitor/>

- `packaging/publish-repo.sh` يبني المستودع ويوقّعه ويدفعه إلى `gh-pages`.
- `.github/workflows/repo.yml` يشغّل النشر يدويًا لإصدار موجود.
- `.github/workflows/release.yml` ينشر المستودع تلقائيًا مع كل وسم جديد إذا
  كان السر `GPG_PRIVATE_KEY` موجودًا.

> ملاحظة: حزمة RPM في الإصدار `v1.0.0` بُنيت بضغط gzip وحجمها 118MB، لذلك
> لا يمكن دفعها إلى `gh-pages` (حد GitHub هو 100MiB للملف). أضفنا ضغط zstd
> في مواصفات RPM؛ أنشئ إصدارًا جديدًا مثل `v1.0.1` وانشر مستودعه.

راجع [`docs/REPOSITORIES_AR.md`](../docs/REPOSITORIES_AR.md) لخطوات إنشاء
المفتاح، وإضافة الأسرار، وتفعيل GitHub Pages، وأوامر التثبيت.

## AUR

حزمة Arch Linux الثنائية موجودة في `packaging/aur/`:

- `PKGBUILD`
- `network-monitor-bin.install`
- `.SRCINFO`

راجع [`packaging/aur/README_AR.md`](aur/README_AR.md) للبناء المحلي وخطوات
النشر في AUR.

## AppImageHub

ملف الإدراج الجاهز موجود في `packaging/appimagehub/Network_Monitor`، مع
تعليمات في [`packaging/appimagehub/README_AR.md`](appimagehub/README_AR.md).

## ملاحظات

- حزم deb/rpm تثبّت المساعد المميز في `/usr/libexec/network-monitor/network-monitor-helper`
  وتضيف سياسة polkit. أول عملية حظر ستطلب كلمة مرور المدير.
- AppImage يحوي المساعد داخله، لكن الحظر يحتاج إلى `pkexec` و`python3` و`nftables` وcgroup v2
  على النظام المضيف. إن لم تتوفر، تعمل المراقبة وتبقى عمليات الحظر غير متاحة.
- الحزم تحوي Python وPySide6 مرفقين، لذلك حجمها أكبر من حزمة تعتمد على حزم النظام.
- وقت التشغيل المرفق يتطلب glibc 2.34 أو أحدث (Ubuntu 22.04+ وDebian 12+ وFedora 35+).
- الترخيص: GPL-3.0-or-later، راجع ملف `LICENSE`.
