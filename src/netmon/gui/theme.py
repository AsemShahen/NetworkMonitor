from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

# Light is the default. Dark is used only when the system reports a dark color
# scheme, GTK_THEME asks for a dark variant, or the user explicitly selects it.
LIGHT = {
    "BG": "#f6f8fa",
    "SURFACE": "#ffffff",
    "SURFACE_2": "#f0f3f6",
    "BORDER": "#d0d7de",
    "TEXT": "#1f2328",
    "MUTED": "#57606a",
    "ACCENT": "#0d9488",
    "ACCENT_HOVER": "#0f766e",
    "ACCENT_2": "#2563eb",
    "ACCENT_TEXT": "#04121a",
    "DOWN": "#0284c7",
    "UP": "#059669",
    "DANGER": "#dc2626",
    "DANGER_TEXT": "#b42318",
    "WARNING": "#d97706",
    "SUCCESS": "#16a34a",
    "BUTTON_HOVER": "#eef2f6",
    "BUTTON_HOVER_BORDER": "#c7d1db",
    "BUTTON_PRESSED": "#e2e8f0",
    "BUTTON_DISABLED": "#8c959f",
    "BUTTON_DISABLED_BORDER": "#d8dee4",
    "SCROLL": "#c7d1db",
    "SCROLL_HOVER": "#aeb9c4",
    "ROW_BORDER": "rgba(208,215,222,0.65)",
}

DARK = {
    "BG": "#0b0f14",
    "SURFACE": "#131a22",
    "SURFACE_2": "#1b2430",
    "BORDER": "#263241",
    "TEXT": "#e6edf3",
    "MUTED": "#8b98a5",
    "ACCENT": "#2dd4bf",
    "ACCENT_HOVER": "#5eead4",
    "ACCENT_2": "#3b82f6",
    "ACCENT_TEXT": "#04121a",
    "DOWN": "#38bdf8",
    "UP": "#34d399",
    "DANGER": "#ef4444",
    "DANGER_TEXT": "#fca5a5",
    "WARNING": "#f59e0b",
    "SUCCESS": "#22c55e",
    "BUTTON_HOVER": "#22303f",
    "BUTTON_HOVER_BORDER": "#334760",
    "BUTTON_PRESSED": "#0f1720",
    "BUTTON_DISABLED": "#56616d",
    "BUTTON_DISABLED_BORDER": "#1e2833",
    "SCROLL": "#2c3a4a",
    "SCROLL_HOVER": "#3a4c61",
    "ROW_BORDER": "rgba(38,50,65,0.5)",
}

_current_colors: dict[str, str] = LIGHT
globals().update(_current_colors)


def resolve_theme(mode: str | None) -> str:
    """Return the effective theme: ``light`` or ``dark``.

    ``system`` follows the platform color scheme.  Environments without a
    desktop theme (including AppImageHub's Xvfb runner) report ``Unknown`` and
    therefore stay light, which is the desired default.
    """
    normalized = (mode or "system").strip().lower()
    if normalized in ("light", "dark"):
        return normalized

    gtk_theme = os.environ.get("GTK_THEME", "").strip().lower()
    if gtk_theme.endswith("-dark") or gtk_theme.endswith(":dark"):
        return "dark"

    # Headless test/CI platforms use Qt's dark default palette.  They are not
    # a user desktop and must not make the application start in dark mode.
    try:
        platform = QGuiApplication.platformName().lower()
    except Exception:
        platform = ""
    if platform in ("offscreen", "minimal"):
        return "light"

    # Without a desktop session there is no reliable system preference.  Use
    # light, which is also what the AppImageHub Xvfb runner expects.
    if not any(
        os.environ.get(key)
        for key in ("XDG_CURRENT_DESKTOP", "DESKTOP_SESSION", "GTK_THEME")
    ):
        return "light"

    try:
        scheme = QGuiApplication.styleHints().colorScheme()
    except Exception:
        scheme = None
    if scheme == Qt.ColorScheme.Dark:
        return "dark"
    return "light"


def _build_palette(colors: dict[str, str]) -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(colors["BG"]))
    palette.setColor(QPalette.WindowText, QColor(colors["TEXT"]))
    palette.setColor(QPalette.Base, QColor(colors["SURFACE"]))
    palette.setColor(QPalette.AlternateBase, QColor(colors["SURFACE_2"]))
    palette.setColor(QPalette.ToolTipBase, QColor(colors["SURFACE_2"]))
    palette.setColor(QPalette.ToolTipText, QColor(colors["TEXT"]))
    palette.setColor(QPalette.Text, QColor(colors["TEXT"]))
    palette.setColor(QPalette.Button, QColor(colors["SURFACE_2"]))
    palette.setColor(QPalette.ButtonText, QColor(colors["TEXT"]))
    palette.setColor(QPalette.BrightText, QColor(colors["DANGER"]))
    palette.setColor(QPalette.Highlight, QColor(colors["ACCENT"]))
    palette.setColor(QPalette.HighlightedText, QColor(colors["ACCENT_TEXT"]))
    palette.setColor(QPalette.PlaceholderText, QColor(colors["MUTED"]))
    palette.setColor(QPalette.Link, QColor(colors["ACCENT_2"]))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(colors["BUTTON_DISABLED"]))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(colors["BUTTON_DISABLED"]))
    return palette


def apply(app, mode: str | None) -> str:
    """Apply the effective theme to the QApplication and module colors."""
    global _current_colors
    resolved = resolve_theme(mode)
    _current_colors = DARK if resolved == "dark" else LIGHT
    globals().update(_current_colors)
    app.setPalette(_build_palette(_current_colors))
    app.setStyleSheet(stylesheet())
    return resolved


def stylesheet() -> str:
    c = _current_colors
    return f"""
* {{
    outline: none;
}}

QWidget {{
    color: {c['TEXT']};
    font-family: "Noto Sans Arabic UI", "Noto Sans Arabic", "IBM Plex Sans Arabic", "Cairo", "Segoe UI", sans-serif;
    font-size: 13px;
}}

QMainWindow, QDialog, QScrollArea {{
    background: {c['BG']};
}}
QScrollArea {{
    border: none;
}}
QWidget#settingsPage, QWidget#tabPage {{
    background: transparent;
}}

QLabel {{
    background: transparent;
}}

QFrame#header {{
    background: {c['SURFACE']};
    border: 1px solid {c['BORDER']};
    border-radius: 14px;
}}
QFrame#card {{
    background: {c['SURFACE']};
    border: 1px solid {c['BORDER']};
    border-radius: 14px;
}}
QFrame#card[accent="down"] {{
    border-top: 2px solid {c['DOWN']};
}}
QFrame#card[accent="up"] {{
    border-top: 2px solid {c['UP']};
}}
QFrame#card[accent="total-down"] {{
    border-top: 2px solid {c['ACCENT_2']};
}}
QFrame#card[accent="total-up"] {{
    border-top: 2px solid {c['ACCENT']};
}}
QFrame#card[accent="count"] {{
    border-top: 2px solid {c['WARNING']};
}}

QLabel#appTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {c['TEXT']};
}}
QLabel#appSubtitle {{
    font-size: 12px;
    color: {c['MUTED']};
}}
QLabel#cardTitle {{
    font-size: 12px;
    color: {c['MUTED']};
}}
QLabel#cardValue {{
    font-size: 22px;
    font-weight: 700;
    color: {c['TEXT']};
}}
QLabel#cardHint {{
    font-size: 11px;
    color: {c['MUTED']};
}}
QLabel#badge {{
    background: {c['SURFACE_2']};
    border: 1px solid {c['BORDER']};
    border-radius: 10px;
    padding: 4px 10px;
    color: {c['MUTED']};
    font-size: 12px;
}}
QLabel#badgeOk {{
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 10px;
    padding: 4px 10px;
    color: {c['SUCCESS']};
    font-size: 12px;
}}
QLabel#badgeWarn {{
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.35);
    border-radius: 10px;
    padding: 4px 10px;
    color: {c['WARNING']};
    font-size: 12px;
}}

QTabWidget::pane {{
    background: {c['BG']};
    border: 1px solid {c['BORDER']};
    border-radius: 14px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {c['MUTED']};
    padding: 9px 18px;
    margin-left: 4px;
    border-radius: 10px;
    font-size: 13px;
}}
QTabBar::tab:hover {{
    color: {c['TEXT']};
    background: {c['SURFACE']};
}}
QTabBar::tab:selected {{
    color: {c['ACCENT_TEXT']};
    background: {c['ACCENT']};
    font-weight: 700;
}}

QTableView {{
    background: {c['SURFACE']};
    alternate-background-color: {c['SURFACE_2']};
    color: {c['TEXT']};
    border: 1px solid {c['BORDER']};
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: rgba(45,212,191,0.18);
    selection-color: {c['TEXT']};
}}
QTableView::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {c['ROW_BORDER']};
}}
QTableView::item:selected {{
    background: rgba(45,212,191,0.16);
}}
QHeaderView {{
    background: {c['SURFACE_2']};
}}
QHeaderView::section {{
    background: {c['SURFACE_2']};
    color: {c['MUTED']};
    padding: 9px 8px;
    border: none;
    border-bottom: 1px solid {c['BORDER']};
    font-weight: 600;
}}
QHeaderView::section:first {{
    border-top-right-radius: 12px;
}}
QHeaderView::section:last {{
    background: {c['SURFACE_2']};
    border-top-left-radius: 12px;
}}
QTableCornerButton::section {{
    background: {c['SURFACE_2']};
    border: none;
}}

QPushButton {{
    background: {c['SURFACE_2']};
    color: {c['TEXT']};
    border: 1px solid {c['BORDER']};
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {c['BUTTON_HOVER']};
    border-color: {c['BUTTON_HOVER_BORDER']};
}}
QPushButton:pressed {{
    background: {c['BUTTON_PRESSED']};
}}
QPushButton:disabled {{
    color: {c['BUTTON_DISABLED']};
    border-color: {c['BUTTON_DISABLED_BORDER']};
}}
QPushButton[variant="primary"] {{
    background: {c['ACCENT']};
    color: {c['ACCENT_TEXT']};
    border: 1px solid {c['ACCENT']};
    font-weight: 700;
}}
QPushButton[variant="primary"]:hover {{
    background: {c['ACCENT_HOVER']};
}}
QPushButton[variant="danger"] {{
    background: rgba(239,68,68,0.14);
    color: {c['DANGER_TEXT']};
    border: 1px solid rgba(239,68,68,0.4);
}}
QPushButton[variant="danger"]:hover {{
    background: rgba(239,68,68,0.24);
}}
QPushButton[variant="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {c['MUTED']};
}}
QPushButton[variant="ghost"]:hover {{
    color: {c['TEXT']};
    background: {c['SURFACE_2']};
}}

QLineEdit, QComboBox, QSpinBox {{
    min-height: 22px;
    background: {c['SURFACE_2']};
    color: {c['TEXT']};
    border: 1px solid {c['BORDER']};
    border-radius: 10px;
    padding: 8px 12px;
    selection-background-color: {c['ACCENT']};
    selection-color: {c['ACCENT_TEXT']};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {c['ACCENT']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {c['SURFACE_2']};
    color: {c['TEXT']};
    border: 1px solid {c['BORDER']};
    selection-background-color: rgba(45,212,191,0.2);
    outline: none;
}}

QCheckBox {{
    spacing: 10px;
    color: {c['TEXT']};
    background: transparent;
    padding: 2px 0;
}}
QCheckBox:disabled {{
    color: {c['MUTED']};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {c['BORDER']};
    background: {c['SURFACE_2']};
}}
QCheckBox::indicator:checked {{
    background: {c['ACCENT']};
    border-color: {c['ACCENT']};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c['SCROLL']};
    border-radius: 6px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['SCROLL_HOVER']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 12px;
    margin: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {c['SCROLL']};
    border-radius: 6px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QStatusBar {{
    background: {c['SURFACE']};
    color: {c['MUTED']};
    border-top: 1px solid {c['BORDER']};
}}
QStatusBar QLabel {{
    color: {c['MUTED']};
}}

QSplitter::handle {{
    background: transparent;
    height: 6px;
}}

QToolTip {{
    background: {c['SURFACE_2']};
    color: {c['TEXT']};
    border: 1px solid {c['BORDER']};
    border-radius: 8px;
    padding: 6px 8px;
}}

QMenu {{
    background: {c['SURFACE_2']};
    color: {c['TEXT']};
    border: 1px solid {c['BORDER']};
    border-radius: 10px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 22px;
    border-radius: 7px;
}}
QMenu::item:selected {{
    background: rgba(45,212,191,0.18);
}}

QGroupBox {{
    background: {c['SURFACE']};
    border: 1px solid {c['BORDER']};
    border-radius: 12px;
    margin-top: 18px;
    padding: 14px 14px 14px 14px;
    font-weight: 700;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top right;
    right: 16px;
    padding: 0 8px;
    color: {c['ACCENT']};
    font-size: 14px;
    font-weight: 700;
}}
QGroupBox QLabel {{
    background: transparent;
}}
"""
