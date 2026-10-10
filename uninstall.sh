#!/usr/bin/env bash
set -e
echo "إزالة مراقب الشبكة..."
sudo rm -f /usr/local/bin/glasswire /usr/local/bin/glasswire-helper
sudo rm -f /usr/share/applications/glasswire.desktop
sudo rm -f /usr/share/icons/hicolor/64x64/apps/glasswire.png
sudo rm -f /usr/share/polkit-1/actions/org.glasswire.helper.policy
sudo rm -f /usr/share/dbus-1/system-services/org.glasswire.helper.service
sudo rm -rf /opt/glasswire
echo "تمت الإزالة"
