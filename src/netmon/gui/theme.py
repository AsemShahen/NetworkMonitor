from __future__ import annotations

BG = "#0b0f14"
SURFACE = "#131a22"
SURFACE_2 = "#1b2430"
BORDER = "#263241"
TEXT = "#e6edf3"
MUTED = "#8b98a5"
ACCENT = "#2dd4bf"
ACCENT_2 = "#3b82f6"
DOWN = "#38bdf8"
UP = "#34d399"
DANGER = "#ef4444"
WARNING = "#f59e0b"
SUCCESS = "#22c55e"

THEME = f"""
* {{
    outline: none;
}}

QWidget {{
    color: {TEXT};
    font-family: "Noto Sans Arabic UI", "Noto Sans Arabic", "IBM Plex Sans Arabic", "Cairo", "Segoe UI", sans-serif;
    font-size: 13px;
}}

QMainWindow, QDialog, QScrollArea {{
    background: {BG};
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
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QFrame#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
QFrame#card[accent="down"] {{
    border-top: 2px solid {DOWN};
}}
QFrame#card[accent="up"] {{
    border-top: 2px solid {UP};
}}
QFrame#card[accent="total-down"] {{
    border-top: 2px solid {ACCENT_2};
}}
QFrame#card[accent="total-up"] {{
    border-top: 2px solid {ACCENT};
}}
QFrame#card[accent="count"] {{
    border-top: 2px solid {WARNING};
}}

QLabel#appTitle {{
    font-size: 20px;
    font-weight: 700;
    color: {TEXT};
}}
QLabel#appSubtitle {{
    font-size: 12px;
    color: {MUTED};
}}
QLabel#cardTitle {{
    font-size: 12px;
    color: {MUTED};
}}
QLabel#cardValue {{
    font-size: 22px;
    font-weight: 700;
    color: {TEXT};
}}
QLabel#cardHint {{
    font-size: 11px;
    color: {MUTED};
}}
QLabel#badge {{
    background: {SURFACE_2};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px 10px;
    color: {MUTED};
    font-size: 12px;
}}
QLabel#badgeOk {{
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 10px;
    padding: 4px 10px;
    color: {SUCCESS};
    font-size: 12px;
}}
QLabel#badgeWarn {{
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.35);
    border-radius: 10px;
    padding: 4px 10px;
    color: {WARNING};
    font-size: 12px;
}}

QTabWidget::pane {{
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {MUTED};
    padding: 9px 18px;
    margin-left: 4px;
    border-radius: 10px;
    font-size: 13px;
}}
QTabBar::tab:hover {{
    color: {TEXT};
    background: {SURFACE};
}}
QTabBar::tab:selected {{
    color: {BG};
    background: {ACCENT};
    font-weight: 700;
}}

QTableView {{
    background: {SURFACE};
    alternate-background-color: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: rgba(45,212,191,0.18);
    selection-color: {TEXT};
}}
QTableView::item {{
    padding: 6px 8px;
    border-bottom: 1px solid rgba(38,50,65,0.5);
}}
QTableView::item:selected {{
    background: rgba(45,212,191,0.16);
}}
QHeaderView {{
    background: {SURFACE_2};
}}
QHeaderView::section {{
    background: {SURFACE_2};
    color: {MUTED};
    padding: 9px 8px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
}}
QHeaderView::section:first {{
    border-top-right-radius: 12px;
}}
QHeaderView::section:last {{
    background: {SURFACE_2};
    border-top-left-radius: 12px;
}}
QTableCornerButton::section {{
    background: {SURFACE_2};
    border: none;
}}

QPushButton {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: #22303f;
    border-color: #334760;
}}
QPushButton:pressed {{
    background: #0f1720;
}}
QPushButton:disabled {{
    color: #56616d;
    border-color: #1e2833;
}}
QPushButton[variant="primary"] {{
    background: {ACCENT};
    color: #04121a;
    border: 1px solid {ACCENT};
    font-weight: 700;
}}
QPushButton[variant="primary"]:hover {{
    background: #5eead4;
}}
QPushButton[variant="danger"] {{
    background: rgba(239,68,68,0.14);
    color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.4);
}}
QPushButton[variant="danger"]:hover {{
    background: rgba(239,68,68,0.24);
}}
QPushButton[variant="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {MUTED};
}}
QPushButton[variant="ghost"]:hover {{
    color: {TEXT};
    background: {SURFACE_2};
}}

QLineEdit, QComboBox, QSpinBox {{
    min-height: 22px;
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    selection-background-color: {ACCENT};
    selection-color: {BG};
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    selection-background-color: rgba(45,212,191,0.2);
    outline: none;
}}

QCheckBox {{
    spacing: 10px;
    color: {TEXT};
    background: transparent;
    padding: 2px 0;
}}
QCheckBox:disabled {{
    color: {MUTED};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {BORDER};
    background: {SURFACE_2};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 4px;
}}
QScrollBar::handle:vertical {{
    background: #2c3a4a;
    border-radius: 6px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: #3a4c61;
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
    background: #2c3a4a;
    border-radius: 6px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

QStatusBar {{
    background: {SURFACE};
    color: {MUTED};
    border-top: 1px solid {BORDER};
}}
QStatusBar QLabel {{
    color: {MUTED};
}}

QSplitter::handle {{
    background: transparent;
    height: 6px;
}}

QToolTip {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 8px;
}}

QMenu {{
    background: {SURFACE_2};
    color: {TEXT};
    border: 1px solid {BORDER};
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
    background: {SURFACE};
    border: 1px solid {BORDER};
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
    color: {ACCENT};
    font-size: 14px;
    font-weight: 700;
}}
QGroupBox QLabel {{
    background: transparent;
}}
"""
