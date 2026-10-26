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
Summary:        Per-application network monitor with blocking
License:        GPL-3.0-or-later
URL:            https://github.com/AsemShahen/NetworkMonitor
BuildArch:      x86_64
Requires:       polkit
Requires:       nftables
Requires:       iproute
Requires:       python3

%description
Network Monitor shows live download and upload speeds for every application,
active connections, executable paths, and session totals. It can block
selected applications with cgroup v2 and nftables through a polkit-authenticated
helper. The interface is available in English and Arabic.

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
* Mon Oct 26 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - %{_version}-1
- Add AppStream metadata
- Use zstd compression for the bundled runtime
* Sun Oct 25 2026 AL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free <asemshahen5@gmail.com> - 1.0.0-1
- Initial package
