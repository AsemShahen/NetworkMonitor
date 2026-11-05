from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from ..updater import UpdateInfo, check_for_update, download_and_install


class UpdateCheckThread(QThread):
    """Check GitHub Releases without blocking the UI."""

    result = Signal(object, str)

    def __init__(self, current_version: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.current_version = current_version

    def run(self) -> None:
        try:
            info = check_for_update(current_version=self.current_version)
        except Exception as exc:  # noqa: BLE001
            self.result.emit(None, str(exc))
            return
        self.result.emit(info, "")


class UpdateInstallThread(QThread):
    """Download, verify, and install an update without blocking the UI."""

    status = Signal(str)
    result = Signal(bool, str)

    def __init__(self, info: UpdateInfo, parent=None) -> None:
        super().__init__(parent)
        self.info = info

    def _progress(self, message: str, percent: int | None = None) -> None:
        if percent is None:
            self.status.emit(message)
        else:
            self.status.emit(f"{message} — {percent}%")

    def run(self) -> None:
        try:
            message = download_and_install(self.info, self._progress)
        except Exception as exc:  # noqa: BLE001
            self.result.emit(False, str(exc))
            return
        self.result.emit(True, message)
