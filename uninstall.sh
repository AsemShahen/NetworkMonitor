#!/usr/bin/env bash
set -e
echo "إزالة مراقب الشبكة..."
USER_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}"
USER_DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user disable --now network-monitor-collector.service >/dev/null 2>&1 || true
fi
rm -f "$USER_CONFIG/systemd/user/network-monitor-collector.service"
rm -f "$USER_DATA/network-monitor/collector-launcher.sh"
sudo rm -f /usr/local/bin/network-monitor /usr/local/bin/network-monitor-helper
sudo rm -f /usr/libexec/network-monitor/network-monitor-helper
sudo rmdir /usr/libexec/network-monitor 2>/dev/null || true
sudo rm -f /usr/share/applications/network-monitor.desktop
sudo rm -f /usr/share/metainfo/network-monitor.metainfo.xml
for size in 64 128 256 512; do
  sudo rm -f "/usr/share/icons/hicolor/${size}x${size}/apps/network-monitor.png"
done
sudo rm -f /usr/share/icons/hicolor/scalable/apps/network-monitor.svg
sudo rm -f /usr/share/polkit-1/actions/org.networkmonitor.helper.policy
sudo rm -f /usr/share/dbus-1/system-services/org.networkmonitor.helper.service
sudo rm -rf /opt/network-monitor
echo "تمت الإزالة. ملفات الإعدادات في ~/.config/network-monitor و~/.local/share/network-monitor بقيت كما هي."
