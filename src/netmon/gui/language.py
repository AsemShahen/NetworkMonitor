from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ..i18n import is_rtl


def apply_language(app: QApplication | None = None) -> None:
    """Apply layout direction and a suitable font for the active language."""
    app = app or QApplication.instance()
    if app is None:
        return
    rtl = is_rtl()
    app.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
    family = "Noto Sans Arabic UI" if rtl else "Noto Sans"
    app.setFont(QFont(family, 10))
