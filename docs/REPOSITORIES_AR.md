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

الإصدارات المستقبلية تُنشر تلقائيًا من `.github/workflows/release.yml` عندما
يكون `GPG_PRIVATE_KEY` مضبوطًا. إن لم يكن السر موجودًا، ينجح الإصدار ويُتخطى
نشر المستودع مع تحذير.

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
- AppImageHub: راجع [`packaging/appimagehub/README_AR.md`](../packaging/appimagehub/README_AR.md).

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
