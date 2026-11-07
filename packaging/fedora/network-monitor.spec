%global _description %{expand:
Network Monitor shows live download and upload speeds for each application
using native Linux Netlink counters, with automatic fallbacks when Netlink is
unavailable. It lists active connections, executable paths, session totals,
and monthly and daily usage with CSV export.

Selected applications can be blocked with cgroup v2 and nftables through a
small PolicyKit-authenticated helper. The interface is available in English
and Arabic and supports right-to-left layouts.}

Name:           network-monitor
Version:        1.0.8
Release:        1%{?dist}
Summary:        Per-application network monitor with usage tracking and blocking
License:        GPL-3.0-or-later
URL:            https://github.com/AsemShahen/NetworkMonitor
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(wheel)
BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  libappstream-glib

Requires:       python3-pyside6
Requires:       python3-pyqtgraph
Requires:       python3-pyroute2
Requires:       python3-numpy
Requires:       nftables
Requires:       iproute
Requires:       polkit

%description
%{_description}

%prep
%autosetup -n NetworkMonitor-%{version}

%generate_buildrequires
%pyproject_buildrequires -r

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files netmon

install -Dm755 bin/network-monitor-helper \
    %{buildroot}%{_libexecdir}/network-monitor/network-monitor-helper
install -Dm644 data/org.networkmonitor.helper.policy \
    %{buildroot}%{_datadir}/polkit-1/actions/org.networkmonitor.helper.policy
install -Dm644 data/network-monitor.desktop \
    %{buildroot}%{_datadir}/applications/network-monitor.desktop
install -Dm644 data/network-monitor.metainfo.xml \
    %{buildroot}%{_datadir}/metainfo/network-monitor.metainfo.xml
install -Dm644 data/network-monitor.1 \
    %{buildroot}%{_mandir}/man1/network-monitor.1
install -Dm644 data/network-monitor.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/network-monitor.svg
for size in 64 128 256 512; do
    install -Dm644 "data/network-monitor-${size}.png" \
        "%{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/network-monitor.png"
done
install -Dm644 /dev/null \
    %{buildroot}%{_datadir}/network-monitor/distro-managed

%check
%pyproject_check_import netmon
desktop-file-validate %{buildroot}%{_datadir}/applications/network-monitor.desktop
if command -v appstream-util >/dev/null 2>&1; then
    appstream-util validate-relax %{buildroot}%{_datadir}/metainfo/network-monitor.metainfo.xml
else
    appstreamcli validate --no-net %{buildroot}%{_datadir}/metainfo/network-monitor.metainfo.xml || test $? -eq 3
fi

%post
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database %{_datadir}/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q %{_datadir}/icons/hicolor >/dev/null 2>&1 || true
fi

%postun
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database %{_datadir}/applications >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q %{_datadir}/icons/hicolor >/dev/null 2>&1 || true
fi

%files -f %{pyproject_files}
%license LICENSE
%doc README.md README_AR.md
%{_bindir}/network-monitor
%{_libexecdir}/network-monitor/network-monitor-helper
%{_datadir}/applications/network-monitor.desktop
%{_datadir}/metainfo/network-monitor.metainfo.xml
%{_datadir}/polkit-1/actions/org.networkmonitor.helper.policy
%{_datadir}/icons/hicolor/64x64/apps/network-monitor.png
%{_datadir}/icons/hicolor/128x128/apps/network-monitor.png
%{_datadir}/icons/hicolor/256x256/apps/network-monitor.png
%{_datadir}/icons/hicolor/512x512/apps/network-monitor.png
%{_datadir}/icons/hicolor/scalable/apps/network-monitor.svg
%{_datadir}/network-monitor/distro-managed
%{_mandir}/man1/network-monitor.1*

%changelog
* Sat Nov 07 2026 Asem Shahen <asemshahen5@gmail.com> - 1.0.8-1
- Initial Fedora package from the upstream 1.0.8 release
- Use distribution-provided Python and Qt dependencies
- Install the PolicyKit helper and mark the package as distro-managed
