from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot


class Worker(QObject):
    """عامل دائم يعمل في خيط مستقل لجمع البيانات وتنفيذ الأوامر."""

    request_snapshot = Signal(bool)
    request_action = Signal(object)

    snapshot_done = Signal(object, object)
    snapshot_error = Signal(str)
    action_done = Signal(bool, str)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.request_snapshot.connect(self._handle_snapshot)
        self.request_action.connect(self._handle_action)

    @Slot(bool)
    def _handle_snapshot(self, include_idle: bool) -> None:
        try:
            rows, summary = self.controller.snapshot(include_idle)
            self.snapshot_done.emit(rows, summary)
        except Exception as exc:  # noqa: BLE001
            self.snapshot_error.emit(str(exc))

    @Slot(object)
    def _handle_action(self, fn) -> None:
        try:
            ok, message = fn()
        except Exception as exc:  # noqa: BLE001
            ok, message = False, str(exc)
        self.action_done.emit(bool(ok), str(message))
