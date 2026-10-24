#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
PREFIX="/opt/network-monitor"

echo "========== تثبيت مراقب الشبكة =========="
echo "المصدر: $ROOT"
echo "الهدف:  $PREFIX"

sudo rm -rf "$PREFIX"
sudo mkdir -p "$PREFIX"
sudo cp -r \
  "$ROOT/python3" "$ROOT/src" "$ROOT/bin" "$ROOT/data" \
  "$ROOT/docs" "$ROOT/packaging" "$ROOT/tests" \
  "$ROOT/README.md" "$ROOT/README_AR.md" "$ROOT/REPORT_AR.md" \
  "$ROOT/pyproject.toml" "$ROOT/install.sh" "$ROOT/uninstall.sh" \
  "$ROOT/network-monitor" \
  "$PREFIX/"

sudo chmod 755 "$PREFIX/network-monitor" "$PREFIX/bin/network-monitor" "$PREFIX/bin/network-monitor-helper"

sudo tee /usr/local/bin/network-monitor >/dev/null <<'WRAP'
#!/bin/sh
exec /opt/network-monitor/network-monitor "$@"
WRAP
sudo chmod 755 /usr/local/bin/network-monitor
sudo install -m 755 "$PREFIX/bin/network-monitor-helper" /usr/local/bin/network-monitor-helper || true

sudo install -m 644 "$PREFIX/data/network-monitor.desktop" /usr/share/applications/network-monitor.desktop
for size in 64 128 256 512; do
  if [ -f "$PREFIX/data/network-monitor-$size.png" ]; then
    sudo install -Dm 644 "$PREFIX/data/network-monitor-$size.png" \
      "/usr/share/icons/hicolor/${size}x${size}/apps/network-monitor.png"
  fi
done
if [ -f "$PREFIX/data/network-monitor.svg" ]; then
  sudo install -Dm 644 "$PREFIX/data/network-monitor.svg" \
    /usr/share/icons/hicolor/scalable/apps/network-monitor.svg
fi

sudo mkdir -p /usr/share/polkit-1/actions
sudo install -m 644 "$PREFIX/data/org.networkmonitor.helper.policy" /usr/share/polkit-1/actions/

if command -v update-desktop-database >/dev/null 2>&1; then
  sudo update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  sudo gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

echo ""
echo "تم التثبيت بنجاح."
echo "شغّل البرنامج من قائمة التطبيقات، أو نفّذ الأمر: network-monitor"
echo "ملاحظة: أول عملية حظر ستطلب كلمة مرور المدير عبر pkexec."
