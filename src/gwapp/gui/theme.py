from __future__ import annotations

THEME = """
QMainWindow, QTabWidget, QFrame, QWidget, QDialog {
    background: #1a1a1f;
    color: #e5e5e5;
    font-size: 12pt;
    font-family: "Noto Sans Arabic UI", "Noto Sans Arabic", "Inter", "Vazirmatn", "Cairo", "Noto Sans", sans-serif;
}

QTabWidget::pane {
    border: 1px solid #2a2a30;
}

QTabBar::tab {
    background: #23232a;
    color: #e5e5e5;
    padding: 8px 16px;
    border: 1px solid #2a2a30;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: #2f6fed;
}

QTableView {
    background: #1f1f24;
    alternate-background-color: #26262c;
    gridline-color: #2a2a30;
    color: #e5e5e5;
}

QHeaderView::section {
    background: #23232a;
    color: #e5e5e5;
    padding: 6px 10px;
    border: none;
    border-right: 1px solid #2a2a30;
    border-bottom: 1px solid #2a2a30;
}

QPushButton {
    background: #23232a;
    color: #e5e5e5;
    border: 1px solid #2a2a30;
    padding: 6px 12px;
}

QPushButton:hover {
    background: #2a2a30;
}

QPushButton:pressed {
    background: #2f6fed;
}

QLineEdit, QComboBox, QSpinBox {
    background: #1f1f24;
    color: #e5e5e5;
    border: 1px solid #2a2a30;
    padding: 4px 6px;
}

QStatusBar {
    background: #23232a;
    color: #e5e5e5;
}
"""
