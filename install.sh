#!/usr/bin/env bash
set -e

echo "========== دليل تثبيت مراقب الشبكة =========="
echo "جارٍ التثبيت في /opt/glasswire..."

sudo mkdir -p /opt/glasswire
sudo cp -r python3 src bin data packaging icons scripts README.md pyproject.toml /opt/glasswire/ 2>/dev/null || true

sudo install -m 755 /opt/glasswire/bin/glasswire /usr/local/bin/glasswire || sudo cp /opt/glasswire/bin/glasswire /usr/local/bin/glasswire
sudo install -m 755 /opt/glasswire/bin/glasswire-helper /usr/local/bin/glasswire-helper || true

sudo install -m 644 /opt/glasswire/data/glasswire.desktop /usr/share/applications/
[ -f /opt/glasswire/data/glasswire.png ] && sudo install -m 644 /opt/glasswire/data/glasswire.png /usr/share/icons/hicolor/64x64/apps/glasswire.png || true

sudo mkdir -p /usr/share/polkit-1/actions
sudo install -m 644 /opt/glasswire/data/org.glasswire.helper.policy /usr/share/polkit-1/actions/

sudo mkdir -p /usr/share/dbus-1/system-services
sudo install -m 644 /opt/glasswire/data/org.glasswire.helper.service /usr/share/dbus-1/system-services/

echo ""
echo "تم التثبيت بنجاح"
echo "يمكنك تشغيل البرنامج من القائمة، أو أمر: glasswire"
