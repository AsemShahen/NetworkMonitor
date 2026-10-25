from __future__ import annotations

from PySide6.QtCore import Qt

from ..i18n import is_rtl
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout


class StatCard(QFrame):
    """بطاقة إحصائية صغيرة تعرض عنواناً وقيمة كبيرة وتلميحاً."""

    def __init__(self, title: str, value: str = "—", hint: str = "", accent: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.setProperty("accent", accent)
        self.setMinimumHeight(92)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        self.value = QLabel(value)
        self.value.setObjectName("cardValue")
        self.hint = QLabel(hint)
        self.hint.setObjectName("cardHint")

        for label in (self.title, self.value, self.hint):
            layout.addWidget(label)
        self.set_rtl(is_rtl())
        layout.addStretch(1)

    def set_rtl(self, rtl: bool) -> None:
        align = (Qt.AlignRight if rtl else Qt.AlignLeft) | Qt.AlignVCenter
        for label in (self.title, self.value, self.hint):
            label.setAlignment(align)

    def set_title(self, title: str) -> None:
        self.title.setText(title)

    def set_hint(self, hint: str) -> None:
        self.hint.setText(hint)

    def set_value(self, value: str, hint: str | None = None) -> None:
        self.value.setText(value)
        if hint is not None:
            self.hint.setText(hint)


class Badge(QLabel):
    def __init__(self, text: str = ""):
        super().__init__(text)
        self.setObjectName("badge")
        self.setAlignment(Qt.AlignCenter)

    def set_state(self, text: str, ok: bool | None = None) -> None:
        self.setText(text)
        if ok is True:
            self.setObjectName("badgeOk")
        elif ok is False:
            self.setObjectName("badgeWarn")
        else:
            self.setObjectName("badge")
        self.style().unpolish(self)
        self.style().polish(self)
