%global debug_package %{nil}

# zstd level 19 keeps the bundled runtime below GitHub Pages' 100 MiB limit.
# gzip produces an RPM that is too large for a git-backed Pages repository.
%global _binary_payload w19.zstdio

# Never turn a build-time interpreter path into a runtime dependency.  The
# bundled runtime is self-contained, and its Python entry points are invoked
# explicitly from the launcher.
%global __requires_exclude ^/home/.*$

Name:           network-monitor
Version:        %{_version}
Release:        1%{?dist}
Summary:        Netlink-based per-application network monitor with monthly usage and blocking
License:        GPL-3.0-or-later
URL:            https://github.com/AsemShahen/NetworkMonitor
BuildArch:      x86_64
Requires:       polkit
Requires:       nftables
Requires:       iproute
Requires:       python3

%description
Network Monitor shows accurate live download and upload speeds for every
application using native Netlink counters, active connections, executable
paths, session totals, and monthly/daily usage. It can block selected
applications with cgroup v2 and nftables through a polkit-authenticated helper.
The interface is available in English and Arabic.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -a %{_sourcedir}/network-monitor-root/. %{buildroot}/
install -Dpm644 %{_sourcedir}/LICENSE %{buildroot}/usr/share/licenses/network-monitor/LICENSE

%post
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

%postun
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

%files
%license /usr/share/licenses/network-monitor/LICENSE
/opt/network-monitor
/usr/bin/network-monitor
/usr/libexec/network-monitor/network-monitor-helper
/usr/share/applications/network-monitor.desktop
/usr/share/metainfo/network-monitor.metainfo.xml
/usr/share/polkit-1/actions/org.networkmonitor.helper.policy
/usr/share/icons/hicolor/64x64/apps/network-monitor.png
/usr/share/icons/hicolor/128x128/apps/network-monitor.png
/usr/share/icons/hicolor/256x256/apps/network-monitor.png
/usr/share/icons/hicolor/512x512/apps/network-monitor.png
/usr/share/icons/hicolor/scalable/apps/network-monitor.svg

%changelog
* Sat Nov 07 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.9-1
- Add distribution-managed install detection for official packages
- Add Debian and Fedora source packaging metadata and validation
- Add AppStream screenshots, developer metadata, and a man page
* Sat Nov 07 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.8-1
- Split the Usage tab into separate Table and Chart inner tabs
- Keep monthly summary cards visible above both Usage views
- Add English and Arabic tab labels with RTL support
* Fri Nov 06 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.7-1
- Add optional background collector systemd user service
- Coordinate SQLite usage writes with a single-writer lock and safe handoff
- Add collector status, enable/disable controls, and generated service units
* Thu Nov 05 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.6-1
- Add signed in-app updates for manual, AppImage, deb, rpm, and Flatpak installs
- Add signed manual update tarball and backup/rollback installation
* Thu Nov 05 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.5-1
- Use native Netlink counters through pyroute2
- Add monthly/daily usage, diagnostics, and autostart
* Mon Oct 26 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.1-1
- Add AppStream metadata
- Use zstd compression for the bundled runtime
* Sun Oct 25 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.0-1
- Initial package
