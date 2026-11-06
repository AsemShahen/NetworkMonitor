# دليل التثبيت على جهاز جديد

## طرق التثبيت السريعة

### Debian / Ubuntu من مستودع APT الموقّع

```bash
sudo install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://asemshahen.github.io/NetworkMonitor/keys/network-monitor.asc \
  | sudo gpg --dearmor --yes -o /etc/apt/keyrings/network-monitor.gpg
echo "deb [signed-by=/etc/apt/keyrings/network-monitor.gpg] https://asemshahen.github.io/NetworkMonitor/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/network-monitor.list
sudo apt update
sudo apt install network-monitor
```

### Fedora / RHEL من مستودع RPM الموقّع

```bash
sudo curl -fsSL https://asemshahen.github.io/NetworkMonitor/rpm/network-monitor.repo \
  -o /etc/yum.repos.d/network-monitor.repo
sudo dnf install network-monitor
```

بصمة مفتاح التوقيع:
`D53CB321C38875CCA82128CC77EED1C545319AE8`.

> إذا أضفت المستودع قبل 2026-10-28، فأعد استيراد المفتاح العام بالأوامر
> أعلاه. أُعيد نشر المستودع بمفتاح توقيع جديد بعد فقدان المفتاح السابق.

### AppImage

```bash
chmod +x NetworkMonitor-<version>-x86_64.AppImage
./NetworkMonitor-<version>-x86_64.AppImage
```

### التحديثات

يملك الإصدار 1.0.6 وما بعده زر **الإعدادات ← تحديثات التطبيق ← التحقق من
التحديثات**. يدعم المحدّث التثبيت اليدوي في `/opt/network-monitor` وAppImage
و`.deb` و`.rpm` وFlatpak، ويتحقق من `SHA256SUMS` و`SHA256SUMS.asc` قبل
التثبيت، ويستخدم `pkexec` لتثبيتات النظام.

إذا كان لديك تثبيت يدوي في `/opt` من 1.0.5 أو أقدم، فثبّت 1.0.7 مرة واحدة:

```bash
tar -xzf NetworkMonitor-1.0.7-linux-x86_64.tar.gz
sudo ./network-monitor/install.sh
```

بعد ذلك يمكن تثبيت الإصدارات اللاحقة من زر التحديث. يحتفظ المحدّث بنسخة
احتياطية مؤرخة في `/opt` ويسترجعها تلقائياً إذا فشل التثبيت اليدوي.

### الجمع في الخلفية (اختياري)

يضيف الإصدار 1.0.7 خيار **الإعدادات ← الجمع في الخلفية ← جمع الاستهلاك
الشهري أثناء إغلاق Network Monitor**. يثبّت الخيار خدمة مستخدم في systemd
ويفعّلها في `~/.config/systemd/user/network-monitor-collector.service`، ولا
يحتاج صلاحيات الجذر.

تستخدم الخدمة قاعدة البيانات نفسها
`~/.local/share/network-monitor/usage.db`. يمنع قفل `flock` لكاتب واحد على
`usage.db.lock` الواجهة والجامع من الكتابة في الوقت نفسه. تسلّم الواجهة دور
الكتابة إلى الجامع عند بدء الخدمة وتستعيده عند تعطيلها.

تُكتب الحالة في `~/.local/share/network-monitor/collector.json`. يمكن تفعيل
الجمع أو تعطيله من الخيار نفسه في الإعدادات؛ وعند تعطيله يعود حساب
الاستهلاك إلى الواجهة أثناء تشغيلها فقط.

يحتاج الخيار إلى جلسة مستخدم systemd عاملة. وإذا لم تكن systemd متاحة
يُعطَّل الخيار ويستمر التطبيق في الحساب أثناء فتحه.

### Arch Linux (AUR)

اسم الحزمة `network-monitor-qt-bin` (بانتظار القبول في AUR):

```bash
yay -S network-monitor-qt-bin
# أو
paru -S network-monitor-qt-bin
```

> الاسم `network-monitor-bin` في AUR يخص مشروعًا آخر (Rust/GTK4).

### التثبيت من المصدر

```bash
git clone https://github.com/AsemShahen/NetworkMonitor.git
cd NetworkMonitor
./install.sh
network-monitor
```

## 1. المتطلبات
- نظام ديبيان/أوبونتو أو فيدورا بنواة حديثة تدعم **cgroup v2**.
- سطح مكتب Wayland أو X11.
- `pyroute2` لعدّادات Netlink. مرفق داخل حزم الإصدار؛ وعند التثبيت من المصدر ثبّته بالأمر `python3 -m pip install pyroute2`.
- `iproute2` (`ss`) رجوع اختياري ويُوصى به.
- `nftables` و`polkit` للحظر.
- عند غياب Netlink و`ss` يكتشف البرنامج الاتصالات من `/proc/net` فقط دون عدّادات بايت. مقابس UDP/QUIC تظهر دائماً «السرعة غير متاحة» لعدم توفر عدّادات موثوقة لها في النواة.

حزم النظام التالية (للقياس الاحتياطي والحظر):

**ديبيان/أوبونتو:**
```bash
sudo apt update
sudo apt install -y iproute2 nftables polkitd pkexec libxcb-cursor0
```

**فيدورا:**
```bash
sudo dnf install -y iproute nftables polkit libxcb
```

> ملاحظة: حزم الإصدار `.deb` و`.rpm` وAppImage تحوي وقت تشغيل مرفقاً (Python وPySide6 وpyqtgraph وnumpy وpyroute2)، فلا يلزم تثبيتها. إذا وُجد `build/runtime` ينسخه `install.sh` إلى `/opt/network-monitor/runtime`؛ وإلا يستخدم التثبيت من المصدر Python النظام.
>
> للحصول على وقت التشغيل المرفق نفسه، نفّذ قبل التثبيت:
>
> ```bash
> ./packaging/build-runtime.sh
> ./install.sh
> ```
>
> وإن لم يتوفر وقت تشغيل مرفق، ثبّت المتطلبات في Python النظام:
>
> ```bash
> python3 -m pip install --user PySide6 pyqtgraph numpy pyroute2
> ```
>
> المساعد المميز يستخدم `python3` النظام (متوفر عادةً في التوزيعات المدعومة).

## 2. نسخ المجلد
انسخ مجلد `Network Monitor` بالكامل إلى الجهاز المستهدف (مثلاً إلى مجلد المنزل).

## 3. التثبيت باستخدام السكريبت
داخل المجلد:
```bash
chmod +x install.sh
./install.sh
```

لا يحتاج السكريبت إلى `sudo` مسبق؛ سيطلبه بنفسه. يقوم بـ:
- نسخ المشروع إلى `/opt/network-monitor`.
- إنشاء مشغّل في `/usr/local/bin/network-monitor` يشير إلى `/opt/network-monitor`.
- تثبيت المساعد المميز في `/usr/libexec/network-monitor/network-monitor-helper`.
- إضافة ملف `.desktop` إلى قائمة التطبيقات.
- تثبيت الأيقونات بعدة أحجام.
- إضافة ملف polkit لطلب الصلاحيات عند الحظر.

## 4. التثبيت اليدوي (بديل)
```bash
sudo rm -rf /opt/network-monitor
sudo mkdir -p /opt/network-monitor
sudo cp -r python3 src bin data docs network-monitor /opt/network-monitor/
sudo chmod +x /opt/network-monitor/network-monitor /opt/network-monitor/bin/network-monitor-helper
printf '#!/bin/sh\nexec /opt/network-monitor/network-monitor "$@"\n' | sudo tee /usr/local/bin/network-monitor >/dev/null
sudo chmod +x /usr/local/bin/network-monitor
sudo install -Dm755 /opt/network-monitor/bin/network-monitor-helper /usr/libexec/network-monitor/network-monitor-helper
sudo cp /opt/network-monitor/data/network-monitor.desktop /usr/share/applications/
sudo cp /opt/network-monitor/data/network-monitor-256.png /usr/share/icons/hicolor/256x256/apps/network-monitor.png
sudo cp /opt/network-monitor/data/org.networkmonitor.helper.policy /usr/share/polkit-1/actions/
```

## 5. التحقق
```bash
network-monitor
```
افتح **الإعدادات ← التشخيص**. الإعداد السليم يعرض:

```text
المحرك: netlink — دقيق
Netlink: متوفر
```

إن ظهر أن Netlink غير متوفر، ثبّت `pyroute2` أو أبقِ `iproute2` مثبتاً ليعمل الرجوع إلى `ss`. أما وضع `/proc/net` الأخير فيعرض الاتصالات فقط مع رسالة أن العدّادات غير متوفرة.

تُخزَّن إحصاءات الاستهلاك الشهرية واليومية في
`~/.local/share/network-monitor/usage.db`، وتُحسب فقط أثناء تشغيل
Network Monitor.

## 6. إلغاء التثبيت
```bash
sudo ./uninstall.sh
```
تُحذف ملفات البرنامج فقط، وتبقى إعداداتك وقائمة الحظر في:
- `~/.config/network-monitor/`
- `~/.local/share/network-monitor/`
