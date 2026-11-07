# Fedora packaging

This is the source-based Fedora spec. Unlike `../network-monitor.spec`, it does
not bundle a Python runtime or PySide6. It uses the distribution packages for
PySide6, pyqtgraph, pyroute2, and NumPy, as required for an official Fedora
review.

## Local build

```bash
sudo dnf install rpm-build rpmdevtools python3-devel pyproject-rpm-macros \
  python3-pyside6 python3-pyqtgraph python3-pyroute2 python3-numpy \
  desktop-file-utils libappstream-glib nftables iproute polkit git
rpmdev-setuptree
git archive --prefix=NetworkMonitor-1.0.8/ \
  --format=tar.gz -o ~/rpmbuild/SOURCES/network-monitor-1.0.8.tar.gz HEAD
cp packaging/fedora/network-monitor.spec ~/rpmbuild/SPECS/
rpmbuild -ba ~/rpmbuild/SPECS/network-monitor.spec
```

The package installs `/usr/share/network-monitor/distro-managed`; the in-app
updater uses this marker to direct users to their package manager instead of
downloading a GitHub package.

## Official submission

Fedora requires a Fedora account, a package review bug, and a reviewer/sponsor.
Submit the spec and a source RPM to a new `Review Request` bug after the build
passes in the CI workflow.
