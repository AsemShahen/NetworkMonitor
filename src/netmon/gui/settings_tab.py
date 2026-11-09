from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..config import BLOCKLIST_FILE, CONFIG_FILE, DATA_DIR, REFRESH_CHOICES
from ..i18n import LANGUAGES, get_language, is_rtl, refresh_label, tr


def _align() -> Qt.AlignmentFlag:
    return (Qt.AlignRight if is_rtl() else Qt.AlignLeft) | Qt.AlignVCenter


class SettingsTab(QWidget):
    interval_changed = Signal(int)
    show_idle_changed = Signal(bool)
    keep_totals_changed = Signal(bool)
    apply_on_start_changed = Signal(bool)
    keep_usage_changed = Signal(bool)
    background_collector_changed = Signal(bool)
    group_cgroups_changed = Signal(bool)
    autostart_changed = Signal(bool)
    minimize_to_tray_changed = Signal(bool)
    language_changed = Signal(str)
    theme_changed = Signal(str)
    reset_totals_requested = Signal()
    apply_blocklist_requested = Signal()
    update_requested = Signal()
    security_settings_changed = Signal(object)

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
        self._diagnostics: dict = {}
        self._diag_text = ""
        self._update_status = tr("update.idle")
        self._update_busy = False
        self._collector_available = True
        self._collector_busy = False
        self._collector_state = "unknown"
        self._collector_updated = 0.0
        self._collector_error = ""

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

        self.theme = QComboBox()
        for code in ("system", "light", "dark"):
            self.theme.addItem("", code)
        current_theme = str(config.get("theme", "system"))
        theme_idx = self.theme.findData(current_theme)
        if theme_idx >= 0:
            self.theme.setCurrentIndex(theme_idx)
        self.theme.setMaximumWidth(240)
        self.theme.currentIndexChanged.connect(self._emit_theme)
        lay.addLayout(self._row("settings.theme", self.theme))

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

        self.keep_usage = QCheckBox()
        self.keep_usage.setChecked(bool(config.get("keep_usage", True)))
        self.keep_usage.toggled.connect(self.keep_usage_changed.emit)
        lay.addWidget(self.keep_usage)

        self.group_cgroups = QCheckBox()
        self.group_cgroups.setChecked(bool(config.get("group_cgroups", True)))
        self.group_cgroups.toggled.connect(self.group_cgroups_changed.emit)
        lay.addWidget(self.group_cgroups)

        self.autostart = QCheckBox()
        self.autostart.setChecked(bool(config.get("autostart", False)))
        self.autostart.toggled.connect(self.autostart_changed.emit)
        lay.addWidget(self.autostart)

        self.minimize_to_tray = QCheckBox()
        self.minimize_to_tray.setChecked(bool(config.get("minimize_to_tray", False)))
        self.minimize_to_tray.toggled.connect(self.minimize_to_tray_changed.emit)
        lay.addWidget(self.minimize_to_tray)

        self._add_hint(lay, "settings.hint.apply")
        self._add_hint(lay, "settings.hint.usage")
        root.addWidget(self.group_monitor)

        # ------------------------------ الجمع في الخلفية ------------------------------
        self.group_collector = QGroupBox()
        clay = QVBoxLayout(self.group_collector)
        clay.setSpacing(10)

        self.background_collector = QCheckBox()
        self.background_collector.setChecked(
            bool(config.get("background_collector", False))
        )
        self.background_collector.toggled.connect(
            self.background_collector_changed.emit
        )
        clay.addWidget(self.background_collector)

        self.collector_status_label = QLabel()
        self.collector_status_label.setObjectName("cardHint")
        self.collector_status_label.setWordWrap(True)
        self.collector_status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        clay.addWidget(self.collector_status_label)

        self._add_hint(clay, "settings.hint.collector")
        root.addWidget(self.group_collector)

        # ----------------------------- الأمان والتهديدات -----------------------------
        self.group_security = QGroupBox()
        slay = QVBoxLayout(self.group_security)
        slay.setSpacing(10)

        self.security_enabled = QCheckBox()
        self.security_enabled.setChecked(bool(config.get("security_enabled", True)))
        self.security_enabled.toggled.connect(self._emit_security)
        slay.addWidget(self.security_enabled)

        self.security_path = QCheckBox()
        self.security_path.setChecked(bool(config.get("security_path_check", True)))
        self.security_path.toggled.connect(self._emit_security)
        slay.addWidget(self.security_path)

        self.security_mining = QCheckBox()
        self.security_mining.setChecked(bool(config.get("security_mining_check", True)))
        self.security_mining.toggled.connect(self._emit_security)
        slay.addWidget(self.security_mining)

        self.security_upload = QCheckBox()
        self.security_upload.setChecked(bool(config.get("security_upload_check", True)))
        self.security_upload.toggled.connect(self._emit_security)
        slay.addWidget(self.security_upload)

        self.security_spike = QDoubleSpinBox()
        self.security_spike.setRange(0.1, 100000.0)
        self.security_spike.setDecimals(1)
        self.security_spike.setSingleStep(0.5)
        self.security_spike.setValue(float(config.get("security_spike_mbps", 5.0)))
        self.security_spike.setSuffix(" MB/s")
        self.security_spike.setMaximumWidth(180)
        self.security_spike.valueChanged.connect(self._emit_security)
        slay.addLayout(self._row("settings.security.spike", self.security_spike))

        self.security_auto = QCheckBox()
        self.security_auto.setChecked(bool(config.get("security_auto_ip_check", False)))
        self.security_auto.toggled.connect(self._emit_security)
        slay.addWidget(self.security_auto)

        self.security_ip_provider = QComboBox()
        self.security_ip_provider.addItem("", "abuseipdb")
        self.security_ip_provider.addItem("", "virustotal")
        self._set_combo_data(
            self.security_ip_provider, str(config.get("security_ip_provider", "abuseipdb"))
        )
        self.security_ip_provider.setMaximumWidth(240)
        self.security_ip_provider.currentIndexChanged.connect(self._emit_security)
        slay.addLayout(self._row("settings.security.ip_provider", self.security_ip_provider))

        self.security_abuse_key = QLineEdit(
            str(config.get("security_abuseipdb_key", "") or "")
        )
        self.security_abuse_key.setEchoMode(QLineEdit.Password)
        self.security_abuse_key.setClearButtonEnabled(True)
        self.security_abuse_key.textChanged.connect(self._emit_security)
        slay.addLayout(self._row("settings.security.abuse_key", self.security_abuse_key))

        self.security_vt_key = QLineEdit(
            str(config.get("security_virustotal_key", "") or "")
        )
        self.security_vt_key.setEchoMode(QLineEdit.Password)
        self.security_vt_key.setClearButtonEnabled(True)
        self.security_vt_key.textChanged.connect(self._emit_security)
        slay.addLayout(self._row("settings.security.vt_key", self.security_vt_key))

        self.security_hash_provider = QComboBox()
        self.security_hash_provider.addItem("", "malwarebazaar")
        self.security_hash_provider.addItem("", "virustotal")
        self._set_combo_data(
            self.security_hash_provider,
            str(config.get("security_hash_provider", "malwarebazaar")),
        )
        self.security_hash_provider.setMaximumWidth(240)
        self.security_hash_provider.currentIndexChanged.connect(self._emit_security)
        slay.addLayout(
            self._row("settings.security.hash_provider", self.security_hash_provider)
        )

        self._add_hint(slay, "settings.hint.security")
        self._add_hint(slay, "settings.hint.security_privacy")
        root.addWidget(self.group_security)

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

        # ------------------------------ تحديثات التطبيق ------------------------------
        self.group_updates = QGroupBox()
        ulay = QVBoxLayout(self.group_updates)
        ulay.setSpacing(10)

        self.update_version_label = QLabel()
        self.update_version_label.setObjectName("cardHint")
        self.update_version_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ulay.addWidget(self.update_version_label)

        self.update_status_label = QLabel()
        self.update_status_label.setObjectName("cardHint")
        self.update_status_label.setWordWrap(True)
        self.update_status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ulay.addWidget(self.update_status_label)

        self.update_btn = QPushButton()
        self.update_btn.setProperty("variant", "primary")
        self.update_btn.clicked.connect(self.update_requested.emit)
        ulay.addWidget(self.update_btn, 0, Qt.AlignLeft)
        root.addWidget(self.group_updates)

        # -------------------------------- التشخيص --------------------------------
        self.group_diagnostics = QGroupBox()
        dlay = QVBoxLayout(self.group_diagnostics)
        dlay.setSpacing(10)
        self.diag_label = QLabel()
        self.diag_label.setObjectName("cardHint")
        self.diag_label.setWordWrap(True)
        self.diag_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        dlay.addWidget(self.diag_label)
        self.copy_diag_btn = QPushButton()
        self.copy_diag_btn.clicked.connect(self._copy_diagnostics)
        dlay.addWidget(self.copy_diag_btn, 0, Qt.AlignLeft)
        root.addWidget(self.group_diagnostics)

        # -------------------------------- حول البرنامج --------------------------------
        self.group_about = QGroupBox()
        alay = QVBoxLayout(self.group_about)
        alay.setSpacing(8)

        self.about_name = QLabel("Network Monitor")
        self.about_name.setObjectName("cardValue")
        alay.addWidget(self.about_name)

        self.author_label = QLabel()
        self.author_label.setObjectName("cardHint")
        self.author_label.setWordWrap(True)
        self.author_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        alay.addWidget(self.author_label)

        self.email_label = QLabel()
        self.email_label.setObjectName("cardHint")
        self.email_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        alay.addWidget(self.email_label)

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
            data="\u202a" + str(DATA_DIR) + "\u202c",
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

    def _emit_theme(self) -> None:
        code = str(self.theme.currentData() or "system")
        self.theme_changed.emit(code)

    def _emit_keep_totals(self, value: bool) -> None:
        self.keep_totals_changed.emit(value)

    def _emit_apply_on_start(self, value: bool) -> None:
        self.apply_on_start_changed.emit(value)

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def security_values(self) -> dict:
        return {
            "security_enabled": self.security_enabled.isChecked(),
            "security_path_check": self.security_path.isChecked(),
            "security_mining_check": self.security_mining.isChecked(),
            "security_upload_check": self.security_upload.isChecked(),
            "security_spike_mbps": float(self.security_spike.value()),
            "security_auto_ip_check": self.security_auto.isChecked(),
            "security_ip_provider": str(
                self.security_ip_provider.currentData() or "abuseipdb"
            ),
            "security_abuseipdb_key": self.security_abuse_key.text().strip(),
            "security_virustotal_key": self.security_vt_key.text().strip(),
            "security_hash_provider": str(
                self.security_hash_provider.currentData() or "malwarebazaar"
            ),
        }

    def _emit_security(self, *_args) -> None:
        self.security_settings_changed.emit(self.security_values())

    # -------------------------------------------------------------- translation
    def retranslate(self) -> None:
        if not self._update_busy:
            self._update_status = tr("update.idle")
        self.group_monitor.setTitle(tr("settings.group.monitor"))
        self.group_collector.setTitle(tr("settings.group.collector"))
        self.group_security.setTitle(tr("settings.group.security"))
        self.group_maintenance.setTitle(tr("settings.group.maintenance"))
        self.group_updates.setTitle(tr("settings.group.updates"))
        self.group_diagnostics.setTitle(tr("settings.group.diagnostics"))
        self.group_about.setTitle(tr("settings.group.about"))

        for label, key in self._labels:
            label.setText(tr(key))
        self.show_idle.setText(tr("settings.show_idle"))
        self.keep_totals.setText(tr("settings.keep_totals"))
        self.apply_on_start.setText(tr("settings.apply_on_start"))
        self.keep_usage.setText(tr("settings.keep_usage"))
        self.background_collector.setText(tr("settings.background_collector"))
        self.group_cgroups.setText(tr("settings.group_cgroups"))
        self.autostart.setText(tr("settings.autostart"))
        self.minimize_to_tray.setText(tr("settings.minimize_to_tray"))
        self.security_enabled.setText(tr("settings.security.enabled"))
        self.security_path.setText(tr("settings.security.path"))
        self.security_mining.setText(tr("settings.security.mining"))
        self.security_upload.setText(tr("settings.security.upload"))
        self.security_auto.setText(tr("settings.security.auto_ip"))
        self.security_abuse_key.setPlaceholderText(tr("settings.security.key_placeholder"))
        self.security_vt_key.setPlaceholderText(tr("settings.security.key_placeholder"))
        for combo, keys in (
            (
                self.security_ip_provider,
                ("settings.security.provider.abuseipdb", "settings.security.provider.virustotal"),
            ),
            (
                self.security_hash_provider,
                ("settings.security.provider.malwarebazaar", "settings.security.provider.virustotal"),
            ),
        ):
            for index, key in enumerate(keys):
                combo.setItemText(index, tr(key))
        self.reset_btn.setText(tr("settings.reset"))
        self.apply_btn.setText(tr("settings.reapply"))
        self.copy_diag_btn.setText(tr("diag.copy"))
        self.update_version_label.setText(tr("update.current", version=__version__))
        self.update_status_label.setText(self._update_status)
        self.update_btn.setText(tr("update.button"))
        self.update_btn.setEnabled(not self._update_busy)

        for label, key, kwargs in self._hints:
            label.setText(tr(key, **kwargs))

        for i, ms in enumerate(REFRESH_CHOICES):
            self.interval.setItemText(i, refresh_label(ms))

        for i, key in enumerate(
            ("settings.theme.system", "settings.theme.light", "settings.theme.dark")
        ):
            self.theme.setItemText(i, tr(key))
        theme_idx = self.theme.findData(str(self.config.get("theme", "system")))
        if theme_idx >= 0:
            self.theme.blockSignals(True)
            self.theme.setCurrentIndex(theme_idx)
            self.theme.blockSignals(False)

        idx = self.language.findData(get_language())
        if idx >= 0:
            self.language.blockSignals(True)
            self.language.setCurrentIndex(idx)
            self.language.blockSignals(False)

        self.author_label.setText(
            tr("settings.author", author="\u202aAL-Asem Software By Asem Shahen And DeepSeek V4.1 Flash Free\u202c")
        )
        self.email_label.setText(
            tr("settings.email", email="\u202aasemshahen5@gmail.com\u202c")
        )
        self._render_engine()
        self._render_diagnostics()
        self._render_collector_status()
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
        self.author_label.setAlignment(align)
        self.email_label.setAlignment(align)
        self.update_version_label.setAlignment(align)
        self.update_status_label.setAlignment(align)
        self.collector_status_label.setAlignment(align)

        self.diag_label.setAlignment(align)
        self.copy_diag_btn.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        self.update_btn.setLayoutDirection(Qt.RightToLeft if rtl else Qt.LeftToRight)
        for group in (
            self.group_monitor,
            self.group_collector,
            self.group_security,
            self.group_maintenance,
            self.group_updates,
            self.group_diagnostics,
            self.group_about,
        ):
            group.setAlignment(Qt.AlignRight if rtl else Qt.AlignLeft)

    def _render_engine(self) -> None:
        state = tr("settings.engine.ready" if self._engine_ok else "settings.engine.limited")
        text = tr("settings.engine", source=self._engine_source, state=state)
        if self._engine_error:
            text += f"\n{self._engine_error}"
        self.engine_label.setText(text)

    def _copy_diagnostics(self) -> None:
        QApplication.clipboard().setText(self._diag_text or self.diag_label.text())

    def _render_diagnostics(self) -> None:
        diag = self._diagnostics or {}
        if not diag:
            self._diag_text = tr("diag.empty")
            self.diag_label.setText(self._diag_text)
            return
        available = tr("env.available")
        unavailable = tr("env.unavailable")
        engine = str(diag.get("engine", "—"))
        state = tr("settings.engine.ready" if diag.get("engine_ok") else "settings.engine.limited")
        lines = [tr("diag.engine", engine=engine, state=state)]
        netlink_error = str(diag.get("netlink_error") or "")
        if netlink_error:
            netlink_error = f" — {netlink_error}"
        lines.append(
            tr(
                "diag.netlink",
                state=available if diag.get("netlink_ok") else unavailable,
                error=netlink_error,
            )
        )
        ss_path = str(diag.get("ss_path") or "")
        if ss_path:
            ss_error = str(diag.get("ss_error") or "")
            if ss_error:
                ss_error = f" — {ss_error}"
            lines.append(
                tr(
                    "diag.ss",
                    path=ss_path,
                    state=available if diag.get("ss_ok") else unavailable,
                    error=ss_error,
                )
            )
        else:
            lines.append(tr("diag.ss_missing"))
        lines.append(
            tr(
                "diag.sockets",
                total=int(diag.get("sockets", 0) or 0),
                tcp=int(diag.get("tcp", 0) or 0),
                udp=int(diag.get("udp", 0) or 0),
            )
        )
        lines.append(
            tr(
                "diag.attributed",
                attributed=int(diag.get("attributed", 0) or 0),
                unattributed=int(diag.get("unattributed", 0) or 0),
            )
        )
        lines.append(
            tr("diag.udp", count=int(diag.get("udp_unmeasured", 0) or 0))
        )
        if diag.get("error"):
            lines.append(tr("diag.error", error=str(diag.get("error"))))
        self._diag_text = "\n".join(line for line in lines if line)
        self.diag_label.setText(self._diag_text)

    # -------------------------------------------------------------------- setters
    def set_engine_text(self, source: str, ok: bool, error: str | None = None) -> None:
        self._engine_source = source
        self._engine_ok = bool(ok)
        self._engine_error = error
        self._render_engine()

    def set_env_text(self, text: str) -> None:
        self._env_value = text
        self.env_label.setText(text)

    def set_collector_available(self, available: bool) -> None:
        self._collector_available = bool(available)
        self.background_collector.setEnabled(
            self._collector_available and not self._collector_busy
        )
        self._render_collector_status()

    def set_collector_busy(self, busy: bool) -> None:
        self._collector_busy = bool(busy)
        self.background_collector.setEnabled(
            self._collector_available and not self._collector_busy
        )

    def set_collector_status(
        self,
        state: str,
        updated: float = 0.0,
        error: str = "",
    ) -> None:
        self._collector_state = str(state or "unknown")
        self._collector_updated = float(updated or 0.0)
        self._collector_error = str(error or "")
        self._render_collector_status()

    def _render_collector_status(self) -> None:
        if not self._collector_available:
            text = tr("collector.status.unavailable")
        elif self._collector_state == "running":
            timestamp = self._collector_updated
            when = (
                datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                if timestamp > 0
                else "—"
            )
            text = tr("collector.status.running", time=when)
        elif self._collector_state == "starting":
            text = tr("collector.status.starting")
        elif self._collector_state == "blocked":
            text = tr("collector.status.blocked")
        elif self._collector_state == "error":
            text = tr(
                "collector.status.error",
                message=self._collector_error or "—",
            )
        elif self._collector_state == "stopped":
            text = tr("collector.status.stopped")
        else:
            text = tr("collector.status.unknown")
        self.collector_status_label.setText(text)
        self.collector_status_label.setToolTip(self._collector_error)

    def set_diagnostics(self, diag: dict) -> None:
        self._diagnostics = dict(diag or {})
        self._render_diagnostics()

    def set_update_status(self, text: str, busy: bool = False) -> None:
        self._update_status = str(text or "")
        self._update_busy = bool(busy)
        self.update_status_label.setText(self._update_status)
        self.update_btn.setEnabled(not self._update_busy)

    def set_update_busy(self, busy: bool) -> None:
        self._update_busy = bool(busy)
        self.update_btn.setEnabled(not self._update_busy)
