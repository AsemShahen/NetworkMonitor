#!/usr/bin/env bash
set -e
echo "إزالة مراقب الشبكة..."
sudo rm -f /usr/local/bin/network-monitor /usr/local/bin/network-monitor-helper
sudo rm -f /usr/share/applications/network-monitor.desktop
for size in 64 128 256 512; do
  sudo rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/network-monitor.png"
done
sudo rm -f /usr/share/icons/hicolor/scalable/apps/network-monitor.svg
sudo rm -f /usr/share/polkit-1/actions/org.networkmonitor.helper.policy
sudo rm -f /usr/share/dbus-1/system-services/org.networkmonitor.helper.service
sudo rm -rf /opt/network-monitor
echo "تمت الإزالة. ملفات الإعدادات في ~/.config/network-monitor و~/.local/share/network-monitor بقيت كما هي."
