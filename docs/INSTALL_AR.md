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
`4E32B2E37802A0EBF4F80C4EF75A8C4DDB4B61EE`.

### AppImage

```bash
chmod +x NetworkMonitor-<version>-x86_64.AppImage
./NetworkMonitor-<version>-x86_64.AppImage
```

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
- حزم النظام التالية (لقياس السرعات والحظر):

**ديبيان/أوبونتو:**
```bash
sudo apt update
sudo apt install -y iproute2 nftables polkitd pkexec libxcb-cursor0
```

**فيدورا:**
```bash
sudo dnf install -y iproute nftables polkit libxcb
```

> ملاحظة: حزمة Python المحمولة `python3/` مرفقة داخل المشروع، لذلك لا يلزم تثبيت Python أو PySide6 لتشغيل الواجهة. المساعد المميز يستخدم `python3` النظام (متوفر عادةً في التوزيعات المدعومة).

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
يجب أن تُفتح النافذة، ويظهر في تبويب «الإعدادات» أن `ss` و`nft` وcgroup v2 متوفرة.

## 6. إلغاء التثبيت
```bash
sudo ./uninstall.sh
```
تُحذف ملفات البرنامج فقط، وتبقى إعداداتك وقائمة الحظر في:
- `~/.config/network-monitor/`
- `~/.local/share/network-monitor/`
