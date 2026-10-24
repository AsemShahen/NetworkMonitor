from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config import BLOCKLIST_FILE, CACHE_DIR, CONFIG_FILE, REFRESH_CHOICES

INTERVALS = REFRESH_CHOICES


def _hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("cardHint")
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    return label


def _row(label: str, widget: QWidget) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(12)
    text = QLabel(label)
    text.setMinimumWidth(190)
    text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    row.addWidget(text)
    row.addWidget(widget, 1)
    row.addStretch(1)
    return row


class SettingsTab(QWidget):
    interval_changed = Signal(int)
    show_idle_changed = Signal(bool)
    keep_totals_changed = Signal(bool)
    apply_on_start_changed = Signal(bool)
    reset_totals_requested = Signal()
    apply_blocklist_requested = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("settingsPage")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        outer.addWidget(scroll)

        page = QWidget()
        page.setObjectName("settingsPage")
        page.setMaximumWidth(960)
        root = QVBoxLayout(page)
        root.setContentsMargins(24, 22, 24, 24)
        root.setSpacing(18)
        scroll.setWidget(page)

        # ------------------------------ الرصد والتحديث ------------------------------
        group = QGroupBox("الرصد والتحديث")
        lay = QVBoxLayout(group)
        lay.setSpacing(12)

        self.interval = QComboBox()
        for label, ms in REFRESH_CHOICES:
            self.interval.addItem(label, ms)
        current = int(config.get("refresh_ms", 30000))
        idx = next((i for i, (_, ms) in enumerate(REFRESH_CHOICES) if ms == current), 2)
        self.interval.setCurrentIndex(idx)
        self.interval.setMaximumWidth(240)
        self.interval.currentIndexChanged.connect(self._emit_interval)
        lay.addLayout(_row("فاصل التحديث:", self.interval))

        self.show_idle = QCheckBox("إظهار العمليات الخاملة (بدون اتصالات نشطة)")
        self.show_idle.setChecked(bool(config.get("show_idle", False)))
        self.show_idle.toggled.connect(self.show_idle_changed.emit)
        lay.addWidget(self.show_idle)

        self.keep_totals = QCheckBox("الاحتفاظ بالإجماليات بين جلسات التشغيل")
        self.keep_totals.setChecked(bool(config.get("keep_totals", True)))
        self.keep_totals.toggled.connect(self._emit_keep_totals)
        lay.addWidget(self.keep_totals)

        self.apply_on_start = QCheckBox("إعادة تطبيق قائمة الحظر عند بدء التشغيل")
        self.apply_on_start.setChecked(bool(config.get("apply_on_start", False)))
        self.apply_on_start.toggled.connect(self._emit_apply_on_start)
        lay.addWidget(self.apply_on_start)

        lay.addWidget(_hint("تُطبَّق التغييرات فورًا ويُحفظ فاصل التحديث تلقائيًا."))
        root.addWidget(group)

        # ----------------------------- الإجماليات والصيانة -----------------------------
        totals_group = QGroupBox("الإجماليات والصيانة")
        tlay = QVBoxLayout(totals_group)
        tlay.setSpacing(12)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.reset_btn = QPushButton("تصفير الإجماليات المحفوظة")
        self.reset_btn.setProperty("variant", "danger")
        self.reset_btn.clicked.connect(self.reset_totals_requested.emit)
        buttons.addWidget(self.reset_btn)
        self.apply_btn = QPushButton("إعادة تطبيق قائمة الحظر الآن")
        self.apply_btn.clicked.connect(self.apply_blocklist_requested.emit)
        buttons.addWidget(self.apply_btn)
        buttons.addStretch(1)
        tlay.addLayout(buttons)

        tlay.addWidget(_hint(
            "قائمة الحظر تُحفظ في \u202a"
            + str(BLOCKLIST_FILE)
            + "\u202c وتُطبَّق عبر مساعد النظام."
        ))
        root.addWidget(totals_group)

        # -------------------------------- حول البرنامج --------------------------------
        about = QGroupBox("حول البرنامج")
        alay = QVBoxLayout(about)
        alay.setSpacing(8)

        name = QLabel("Network Monitor")
        name.setObjectName("cardValue")
        alay.addWidget(name)

        self.engine_label = QLabel("محرك القياس: —")
        self.engine_label.setWordWrap(True)
        self.engine_label.setObjectName("cardHint")
        self.engine_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        alay.addWidget(self.engine_label)

        self.env_label = QLabel("—")
        self.env_label.setWordWrap(True)
        self.env_label.setObjectName("cardHint")
        self.env_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        alay.addWidget(self.env_label)

        alay.addWidget(_hint(
            "الإعدادات: \u202a" + str(CONFIG_FILE)
            + "\u202c\nالبيانات: \u202a" + str(CACHE_DIR) + "\u202c"
        ))
        root.addWidget(about)

        root.addStretch(1)

    def _emit_interval(self) -> None:
        ms = int(self.interval.currentData())
        self.interval_changed.emit(ms)

    def _emit_keep_totals(self, value: bool) -> None:
        self.keep_totals_changed.emit(value)

    def _emit_apply_on_start(self, value: bool) -> None:
        self.apply_on_start_changed.emit(value)

    def set_engine_text(self, source: str, ok: bool, error: str | None = None) -> None:
        state = "جاهز" if ok else "محدود"
        text = f"محرك القياس: {source} — {state}"
        if error:
            text += f"\n{error}"
        self.engine_label.setText(text)

    def set_env_text(self, text: str) -> None:
        self.env_label.setText(text)
