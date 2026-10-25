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
from ..i18n import LANGUAGES, get_language, is_rtl, refresh_label, tr


def _align() -> Qt.AlignmentFlag:
    return (Qt.AlignRight if is_rtl() else Qt.AlignLeft) | Qt.AlignVCenter


class SettingsTab(QWidget):
    interval_changed = Signal(int)
    show_idle_changed = Signal(bool)
    keep_totals_changed = Signal(bool)
    apply_on_start_changed = Signal(bool)
    language_changed = Signal(str)
    reset_totals_requested = Signal()
    apply_blocklist_requested = Signal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("settingsPage")
        self._labels: list[tuple[QLabel, str]] = []
        self._hints: list[tuple[QLabel, str, dict]] = []
        self._engine_source = "—"
        self._engine_ok = False
        self._engine_error: str | None = None
        self._env_value = "—"

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
        self.group_monitor = QGroupBox()
        lay = QVBoxLayout(self.group_monitor)
        lay.setSpacing(12)

        self.language = QComboBox()
        for code, name in LANGUAGES:
            self.language.addItem(name, code)
        idx = self.language.findData(get_language())
        if idx >= 0:
            self.language.setCurrentIndex(idx)
        self.language.setMaximumWidth(240)
        self.language.currentIndexChanged.connect(self._emit_language)
        lay.addLayout(self._row("settings.language", self.language))

        self.interval = QComboBox()
        for ms in REFRESH_CHOICES:
            self.interval.addItem(refresh_label(ms), ms)
        current = int(config.get("refresh_ms", 30000))
        idx = next((i for i, ms in enumerate(REFRESH_CHOICES) if ms == current), 2)
        self.interval.setCurrentIndex(idx)
        self.interval.setMaximumWidth(240)
        self.interval.currentIndexChanged.connect(self._emit_interval)
        lay.addLayout(self._row("settings.interval", self.interval))

        self.show_idle = QCheckBox()
        self.show_idle.setChecked(bool(config.get("show_idle", False)))
        self.show_idle.toggled.connect(self.show_idle_changed.emit)
        lay.addWidget(self.show_idle)

        self.keep_totals = QCheckBox()
        self.keep_totals.setChecked(bool(config.get("keep_totals", True)))
        self.keep_totals.toggled.connect(self._emit_keep_totals)
        lay.addWidget(self.keep_totals)

        self.apply_on_start = QCheckBox()
        self.apply_on_start.setChecked(bool(config.get("apply_on_start", False)))
        self.apply_on_start.toggled.connect(self._emit_apply_on_start)
        lay.addWidget(self.apply_on_start)

        self._add_hint(lay, "settings.hint.apply")
        root.addWidget(self.group_monitor)

        # ----------------------------- الإجماليات والصيانة -----------------------------
        self.group_maintenance = QGroupBox()
        tlay = QVBoxLayout(self.group_maintenance)
        tlay.setSpacing(12)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        self.reset_btn = QPushButton()
        self.reset_btn.setProperty("variant", "danger")
        self.reset_btn.clicked.connect(self.reset_totals_requested.emit)
        buttons.addWidget(self.reset_btn)
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self.apply_blocklist_requested.emit)
        buttons.addWidget(self.apply_btn)
        buttons.addStretch(1)
        tlay.addLayout(buttons)

        self._add_hint(
            tlay,
            "settings.hint.blocklist",
            path="\u202a" + str(BLOCKLIST_FILE) + "\u202c",
        )
        root.addWidget(self.group_maintenance)

        # -------------------------------- حول البرنامج --------------------------------
        self.group_about = QGroupBox()
        alay = QVBoxLayout(self.group_about)
        alay.setSpacing(8)

        self.about_name = QLabel("Network Monitor")
        self.about_name.setObjectName("cardValue")
        alay.addWidget(self.about_name)

        self.engine_label = QLabel()
        self.engine_label.setWordWrap(True)
        self.engine_label.setObjectName("cardHint")
        alay.addWidget(self.engine_label)

        self.env_label = QLabel()
        self.env_label.setWordWrap(True)
        self.env_label.setObjectName("cardHint")
        alay.addWidget(self.env_label)

        self._add_hint(
            alay,
            "settings.hint.paths",
            config="\u202a" + str(CONFIG_FILE) + "\u202c",
            data="\u202a" + str(CACHE_DIR) + "\u202c",
        )
        root.addWidget(self.group_about)

        root.addStretch(1)
        self.retranslate()

    # ------------------------------------------------------------------ helpers
    def _row(self, label_key: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        text = QLabel()
        text.setMinimumWidth(190)
        self._labels.append((text, label_key))
        row.addWidget(text)
        row.addWidget(widget, 1)
        row.addStretch(1)
        return row

    def _add_hint(self, layout: QVBoxLayout, key: str, **kwargs) -> None:
        label = QLabel()
        label.setObjectName("cardHint")
        label.setWordWrap(True)
        self._hints.append((label, key, kwargs))
        layout.addWidget(label)

    def _emit_interval(self) -> None:
        self.interval_changed.emit(int(self.interval.currentData()))

    def _emit_language(self) -> None:
        code = str(self.language.currentData() or "en")
        self.language_changed.emit(code)

    def _emit_keep_totals(self, value: bool) -> None:
        self.keep_totals_changed.emit(value)

    def _emit_apply_on_start(self, value: bool) -> None:
        self.apply_on_start_changed.emit(value)

    # -------------------------------------------------------------- translation
    def retranslate(self) -> None:
        self.group_monitor.setTitle(tr("settings.group.monitor"))
        self.group_maintenance.setTitle(tr("settings.group.maintenance"))
        self.group_about.setTitle(tr("settings.group.about"))

        for label, key in self._labels:
            label.setText(tr(key))
        self.show_idle.setText(tr("settings.show_idle"))
        self.keep_totals.setText(tr("settings.keep_totals"))
        self.apply_on_start.setText(tr("settings.apply_on_start"))
        self.reset_btn.setText(tr("settings.reset"))
        self.apply_btn.setText(tr("settings.reapply"))

        for label, key, kwargs in self._hints:
            label.setText(tr(key, **kwargs))

        for i, ms in enumerate(REFRESH_CHOICES):
            self.interval.setItemText(i, refresh_label(ms))

        idx = self.language.findData(get_language())
        if idx >= 0:
            self.language.blockSignals(True)
            self.language.setCurrentIndex(idx)
            self.language.blockSignals(False)

        self._render_engine()
        self.env_label.setText(self._env_value)
        self._apply_direction()

    def _apply_direction(self) -> None:
        rtl = is_rtl()
        self.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        align = _align()
        for label, _ in self._labels:
            label.setAlignment(align)
        for label, _, _ in self._hints:
            label.setAlignment(align)
        self.engine_label.setAlignment(align)
        self.env_label.setAlignment(align)
        self.about_name.setAlignment(align)

        for group in (self.group_monitor, self.group_maintenance, self.group_about):
            group.setAlignment(Qt.AlignRight if rtl else Qt.AlignLeft)

    def _render_engine(self) -> None:
        state = tr("settings.engine.ready" if self._engine_ok else "settings.engine.limited")
        text = tr("settings.engine", source=self._engine_source, state=state)
        if self._engine_error:
            text += f"\n{self._engine_error}"
        self.engine_label.setText(text)

    # -------------------------------------------------------------------- setters
    def set_engine_text(self, source: str, ok: bool, error: str | None = None) -> None:
        self._engine_source = source
        self._engine_ok = bool(ok)
        self._engine_error = error
        self._render_engine()

    def set_env_text(self, text: str) -> None:
        self._env_value = text
        self.env_label.setText(text)
