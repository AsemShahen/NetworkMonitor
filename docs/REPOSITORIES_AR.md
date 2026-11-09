# مستودعات الحزم الموقّعة

يمكن تثبيت Network Monitor من مستودع APT موقّع (Debian/Ubuntu) ومستودع RPM
موقّع (Fedora/RHEL). يُنشر المستودع في فرع `gh-pages` وتخدمه GitHub Pages:

<https://asemshahen.github.io/NetworkMonitor/>

يحتوي المستودع على:

- `apt/` — بيانات APT و`InRelease` و`Release.gpg` ومجلد حزم `.deb`.
- `rpm/` — بيانات RPM و`repomd.xml` الموقّع وحزم `.rpm`.
- `keys/network-monitor.asc` — المفتاح العام للتوقيع.
- `keys/fingerprint.txt` — بصمة المفتاح.

السكريبت `packaging/publish-repo.sh` يبني المستودع من الحزم الموجودة في
`build/`، ويوقّع البيانات الوصفية، ثم يدفعه إلى `gh-pages` عند
`PUBLISH=1`. ينشر شجرة جديدة تحتوي على الحزم الحالية فقط؛ تبقى الإصدارات
القديمة متاحة على GitHub Releases. هذا يحافظ على حجم موقع Pages وتاريخ git
صغيرين.

## حزم المستودع الحالية (v1.1.0)

يخدم المستودع حاليًا أصول الإصدار `v1.1.0` الرسمية، لذلك تطابق هذه البصمات
`SHA256SUMS` ومصدر AUR.

تبقى إصدارات `v1.0.2` حتى `v1.0.9` متاحة على GitHub Releases. ويخدم
المستودع الآن `v1.1.0` موقّعًا بالمفتاح الحالي. العملاء الحاليون يثقون
بالبصمة السابقة أدناه، وعليهم استيراد المفتاح العام الجديد قبل تحديث `apt`
أو `dnf` التالي.

- `.deb`: `92,341,976` بايت، SHA-256
  `02749e5dbe4e026ff45776deb771410c0255a7d98cb94efcc2e3dab1303f6a4a`
- `.rpm`: `93,079,874` بايت، SHA-256
  `9307bbb01f4009a352ff2e5ed9bcb3fc848862ef3079c169ed6878c370f4952c`
- أرشيف التحديث اليدوي: `125,051,321` بايت، SHA-256
  `a79b823d6381845a286fa075171dd26694faca6fa78ddee9e823957827d3ce63`
- AppImage: `112,024,056` بايت، SHA-256
  `5ca74cd95e8c520fb504835fcdd4c89255e7311fbb8037863f8a090ccf8898ec`
- AppImage zsync: `191,694` بايت، SHA-256
  `ccd29e39c4b98f43a03327c9b821144b8761878eb111c12c099b3a7f166dceee`
- البصمة السابقة (للعملاء المثبتين قبل 2026-10-28):
  `4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`
- البصمة الحالية:
  `D53CB321C38875CCA82128CC77EED1C545319AE8`

### ترحيل عملاء APT/RPM الحاليين

بعد إعادة نشر المستودع، يستورد العملاء الحاليون المفتاح العام الجديد مرة واحدة.

APT:

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
sudo apt update
```

RPM:

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  -o /etc/pki/rpm-gpg/RPM-GPG-KEY-network-monitor
sudo rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-network-monitor
sudo dnf clean all
sudo dnf makecache
```

حزمة AUR تستخدم ملف `.deb` الرسمي للإصدار `v1.1.0`.

## الإعداد لمرة واحدة

### 1. إنشاء مفتاح التوقيع

نفّذ هذا على جهاز موثوق، وليس داخل CI:

```bash
gpg --full-generate-key
```

المقترح: RSA 4096، صلاحية سنتين، اسم واضح مثل `Network Monitor packages`،
وبريد المشروع.

اعرف البصمة وصدّر المفتاحين:

```bash
KEY_ID=$(gpg --list-secret-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}')
echo "$KEY_ID"
gpg --armor --export-secret-keys "$KEY_ID" > network-monitor-private.asc
gpg --armor --export "$KEY_ID" > network-monitor-public.asc
```

احتفظ بالملف الخاص بعيدًا عن المستودع، واحذفه بعد إضافة السر إلى GitHub.

### 2. إضافة أسرار GitHub Actions

من المستودع: **Settings → Secrets and variables → Actions → New repository secret**.

- `GPG_PRIVATE_KEY` — محتوى `network-monitor-private.asc` كاملًا.
- `GPG_PASSPHRASE` — عبارة مرور المفتاح إن وجدت. اتركها غير موجودة إن كان
  المفتاح بلا عبارة مرور.
- `GPG_KEY_ID` — اختياري؛ السكريبت يستخرج البصمة تلقائيًا.

لا ترفع المفتاح الخاص أو عبارة المرور إلى المستودع.

### 3. نشر المستودع لأول مرة

شغّل **Actions → Publish package repository → Run workflow** مع وسم إصدار
موجود بُني بعد تغيير ضغط zstd، مثل `v1.0.1`.

سيُنزّل سير العمل ملفي `.deb` و`.rpm` من الإصدار، ويبني البيانات الوصفية،
ويوقّعها، وينشئ فرع `gh-pages` إن لم يكن موجودًا، ثم يدفعه.

يرفض GitHub الملفات الأكبر من 100MiB داخل مستودع git. أصبحت حزمة RPM
تستخدم ضغط zstd بالمستوى 19 لتبقى تحت هذا الحد. إذا كنت تنشر إصدارًا قديمًا
بُنيت حزمته بـgzip (مثل `v1.0.0`)، فأنشئ إصدارًا جديدًا من المصدر الحالي
وانشر وسمه بدلًا منه. يظل GitHub Releases قادرًا على استضافة الملف القديم
الأكبر.

### 4. تفعيل GitHub Pages

بعد نجاح التشغيل الأول، افتح **Settings → Pages** واختر:

- **Source:** Deploy from a branch
- **Branch:** `gh-pages`
- **Folder:** `/ (root)`

ثم احفظ. سيصبح المستودع متاحًا على:

<https://asemshahen.github.io/NetworkMonitor/>

النشر التلقائي للمستودع من `.github/workflows/release.yml` مُقيّد بمتغير
المستودع `PUBLISH_SIGNED_REPOSITORY=true`. أُنشئ المفتاح الجديد في
2026-10-28، ويُحفظ المفتاح الخاص وعبارة المرور محليًا ولا يُرفعان إلى
المستودع. أُعيد نشر المستودع بـ`v1.1.0` في 2026-11-09، ويجتاز كل من
`InRelease` و`repomd.xml.asc` التحقق بالبصمة الجديدة.

المفتاح السابق (`4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`) غير قابل
للاستعادة. المفتاح الجديد يستبدله؛ وعلى العملاء الحاليين تنفيذ أوامر الترحيل
أعلاه.

## التثبيت من المستودع

### Debian / Ubuntu

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
echo "deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] https://asemshahen.github.io/NetworkMonitor/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/network-monitor.list
sudo apt update
sudo apt install network-monitor
```

### Fedora / RHEL

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/rpm/network-monitor.repo \
  -o /etc/yum.repos.d/network-monitor.repo
sudo dnf install network-monitor
```

مستودع RPM يستخدم `repo_gpgcheck=1`: يتحقق DNF من توقيع `repomd.xml` ومن
بصمات الحزم الموجودة داخله. توقيع الحزم نفسها على مستوى RPM غير مفعّل بعد
(`gpgcheck=0`).

## التحقق اليدوي من التوقيعات

```bash
base=https://asemshahen.github.io/NetworkMonitor
curl -fsSL "$base/keys/network-monitor.asc" | gpg --import
curl -fsSL "$base/apt/dists/stable/InRelease" -o /tmp/InRelease
gpg --verify /tmp/InRelease
curl -fsSL "$base/rpm/x86_64/repodata/repomd.xml" -o /tmp/repomd.xml
curl -fsSL "$base/rpm/x86_64/repodata/repomd.xml.asc" -o /tmp/repomd.xml.asc
gpg --verify /tmp/repomd.xml.asc /tmp/repomd.xml
```

قارن البصمة مع `keys/fingerprint.txt` ومع المفتاح الذي أنشأته.

## بناء المستودع محليًا دون دفعه

```bash
PUBLISH=0 ./packaging/publish-repo.sh
```

تظهر المخرجات في `build/repo/`. تحتاج إلى `apt-ftparchive` و`createrepo_c`
(أو `createrepo`) و`gpg`، ومفتاح توقيع في حلقة مفاتيحك.

## AUR وAppImageHub

- Arch Linux: راجع [`packaging/aur/README_AR.md`](../packaging/aur/README_AR.md).
  اسم حزمة AUR هو `network-monitor-qt-bin` (الاسم `network-monitor-bin`
  مستخدم لمشروع آخر).
- AppImageHub: راجع [`packaging/appimagehub/README_AR.md`](../packaging/appimagehub/README_AR.md)
  أو النسخة الإنجليزية [`README.md`](../packaging/appimagehub/README.md).

## حل المشكلات

- **GitHub Pages يعيد 404:** تأكد من وجود فرع `gh-pages` ومن اختياره في
  إعدادات Pages.
- **رفض دفع `gh-pages`:** أزل حماية الفرع عن `gh-pages`؛ فهو فرع مولّد
  يُستبدل عند كل نشر.
- **`createrepo_c: command not found`:** ثبّت `createrepo-c` على
  Ubuntu/Debian أو `createrepo_c` على Fedora.
- **`GPG_PRIVATE_KEY is not configured`:** أضف السر ثم أعد تشغيل سير العمل.
- **`is larger than GitHub's ... limit`:** بُنيت الحزمة دون ضغط zstd؛ أنشئ
  إصدارًا جديدًا من المصدر الحالي وانشر وسمه.
- **APT يعرض `NO_PUBKEY`:** أعد تثبيت المفتاح بالأمر أعلاه، ولا تستخدم
  `[trusted=yes]`.
- **DNF يرفض توقيع `repomd.xml`:** تأكد من أن رابط `gpgkey` يعمل ومن وجود
  `repomd.xml.asc`.
