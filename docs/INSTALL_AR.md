# دليل التثبيت على جهاز جديد

## 1. نسخ المجلد
انسخ مجلد `GlassWire` بالكامل إلى الجهاز المستهدف.

## 2. التثبيت باستخدام السكريبت
داخل المجلد:
```bash
chmod +x install.sh
sudo ./install.sh
```

يقوم السكريبت بـ:
- نسخ الملفات إلى /opt/glasswire
- إنشاء اختصار في /usr/local/bin/glasswire
- إضافة ملف .desktop لقائمة التطبيقات
- إضافة ملف polkit لطلب الصلاحيات عند الحاجة
- إضافة ملف D-Bus للخدمة المميزة

## 3. التثبيت اليدوي (بديل)
```bash
sudo mkdir -p /opt/glasswire
sudo cp -r python3 src bin /opt/glasswire/
sudo ln -s /opt/glasswire/bin/glasswire /usr/local/bin/glasswire 2>/dev/null || sudo cp /opt/glasswire/bin/glasswire /usr/local/bin/glasswire
```

## 4. التحقق
```bash
glasswire --help 2>/dev/null || glasswire
```
