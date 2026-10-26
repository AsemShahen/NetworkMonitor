# حزمة AUR: `network-monitor-bin`

هذه حزمة ثنائية لمستخدمي Arch Linux. تنزّل ملف `.deb` الرسمي من GitHub
Releases وتستخرج منه نفس الملفات: التطبيق، المساعد المميز، سياسة polkit،
الأيقونات، وملف سطح المكتب.

## البناء والاختبار محليًا

```bash
cd packaging/aur
makepkg -si
network-monitor
```

الأدوات المطلوبة: `base-devel`، و`binutils` (يوفر `ar`)، و`zstd` (لفك ضغط
`data.tar.zst`).

## تحديث الإصدار

عند إصدار جديد:

1. غيّر `pkgver` في `PKGBUILD`.
2. احسب بصمة ملف `.deb` الجديد:

```bash
sha256sum network-monitor_<version>_amd64.deb
```

3. ضع البصمة في `sha256sums`.
4. أعد توليد `.SRCINFO`:

```bash
makepkg --printsrcinfo > .SRCINFO
```

## النشر في AUR

1. أضف مفتاح SSH إلى حساب AUR من:
   <https://aur.archlinux.org/account/>
2. استنسخ مستودع الحزمة:

```bash
git clone ssh://aur@aur.archlinux.org/network-monitor-bin.git
cd network-monitor-bin
cp /path/to/NetworkMonitor/packaging/aur/PKGBUILD .
cp /path/to/NetworkMonitor/packaging/aur/network-monitor-bin.install .
cp /path/to/NetworkMonitor/packaging/aur/.SRCINFO .
git add PKGBUILD network-monitor-bin.install .SRCINFO
git commit -m "Initial import: network-monitor-bin 1.0.0"
git push
```

بعد القبول سيستطيع المستخدمون التثبيت عبر:

```bash
yay -S network-monitor-bin
# أو
paru -S network-monitor-bin
```

## ملاحظات

- الحزمة `-bin` تغلّف ملف `.deb` الرسمي؛ لذلك لا تحتاج إلى بناء وقت التشغيل
  من المصدر.
- `provides` و`conflicts` يمنعان تثبيت حزمة `network-monitor` الأصلية في الوقت
  نفسه.
- الحزمة ليست في مستودع Arch الرسمي؛ AUR مستودع مجتمعي. للدخول إلى المستودع
  الرسمي لاحقًا ستحتاج إلى حزمة تبني من المصدر وتعتمد على حزم النظام، ثم
  تصويت Trusted User.
