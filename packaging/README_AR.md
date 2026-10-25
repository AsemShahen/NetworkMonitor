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
2. ارفع المشروع إلى الفرع `main`.
3. أنشئ وسم إصدار وادفعه:

```bash
git tag v1.0.0
git push origin v1.0.0
```

سيعمل سير العمل `.github/workflows/release.yml` تلقائيًا، ويبني الحزم الثلاث،
وينشئ Release ويحمّل الملفات إليه. يمكن أيضًا تشغيله يدويًا من تبويب Actions
مع إدخال رقم الإصدار.

## ملاحظات

- حزم deb/rpm تثبّت المساعد المميز في `/usr/libexec/network-monitor/network-monitor-helper`
  وتضيف سياسة polkit. أول عملية حظر ستطلب كلمة مرور المدير.
- AppImage يحوي المساعد داخله، لكن الحظر يحتاج إلى `pkexec` و`python3` و`nftables` وcgroup v2
  على النظام المضيف. إن لم تتوفر، تعمل المراقبة وتبقى عمليات الحظر غير متاحة.
- الحزم تحوي Python وPySide6 مرفقين، لذلك حجمها أكبر من حزمة تعتمد على حزم النظام.
- الترخيص: GPL-3.0-or-later، راجع ملف `LICENSE`.
