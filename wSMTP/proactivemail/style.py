"""
style.py — PyQt5 uygulama stili (koyu tema).
"""
import platform as _plt

_PLATFORM = _plt.system()
_SYS_FONT = ("'SF Pro Display', Helvetica" if _PLATFORM == "Darwin"
             else "'Segoe UI'" if _PLATFORM == "Windows"
             else "'Ubuntu', 'Noto Sans'")

APP_STYLE = (
    "* { font-family: " + _SYS_FONT + """, sans-serif; }
QMainWindow, QWidget#root { background: #1a1a2e; }
QWidget { background: transparent; color: #e8e4d9; }
QWidget#panel { background: #16213e; border-right: 1px solid #0f3460; }
QWidget#preview_panel { background: #1a1a2e; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 6px; background: transparent; border: none; }
QScrollBar::handle:vertical { background: #0f3460; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QPushButton {
    background: #0f3460; color: #e8e4d9; border: none;
    border-radius: 8px; padding: 8px 18px; font-size: 13px; font-weight: 600;
}
QPushButton:hover { background: #16213e; border: 1px solid #e94560; }
QPushButton:pressed { background: #e94560; color: #fff; }
QPushButton#accent { background: #e94560; color: #fff; }
QPushButton#accent:hover { background: #ff6b81; }
QPushButton#ghost {
    background: transparent; border: 1px solid #0f3460;
    color: #a0a0c0; font-size: 12px; padding: 6px 14px;
}
QPushButton#ghost:hover { border-color: #e94560; color: #e94560; }
QPushButton#save_btn { background: #27ae60; color: #fff; font-size: 14px; padding: 10px 28px; }
QPushButton#save_btn:hover { background: #2ecc71; }
QPushButton#lang_btn {
    background: #0f3460; color: #e8e4d9; border: 1px solid #e94560;
    border-radius: 8px; padding: 6px 14px; font-size: 12px;
}
QPushButton#lang_btn:hover { background: #e94560; color: #fff; }
QLabel#title { font-size: 20px; font-weight: 700; color: #e94560; letter-spacing: 1px; }
QLabel#section { font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #5a5a8a; }
QLabel#subtitle { font-size: 12px; color: #7070a0; }
QLineEdit, QTextEdit {
    background: #0d1b2a; border: 1px solid #0f3460;
    border-radius: 7px; color: #e8e4d9; padding: 7px 11px; font-size: 13px;
    selection-background-color: #e94560;
}
QLineEdit:focus, QTextEdit:focus { border: 1px solid #e94560; }
QComboBox {
    background: #0d1b2a; border: 1px solid #0f3460; border-radius: 7px;
    color: #e8e4d9; padding: 6px 12px; font-size: 13px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #0d1b2a; border: 1px solid #e94560;
    color: #e8e4d9; selection-background-color: #e94560;
}
QFrame#block_card {
    background: #0d1b2a; border: 1px solid #0f3460; border-radius: 10px; margin: 3px 0;
}
QFrame#block_card:hover { border-color: #e94560; cursor: grab; }
QToolButton {
    background: transparent; border: 1px solid #0f3460;
    border-radius: 5px; color: #7070a0; font-size: 13px; padding: 2px;
}
QToolButton:hover { border-color: #e94560; color: #e94560; }
QGroupBox {
    font-size: 11px; font-weight: 700; letter-spacing: 1.5px;
    color: #5a5a8a; border: 1px solid #0f3460; border-radius: 10px;
    margin-top: 14px; padding: 14px 12px 10px 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; background: #16213e; }
""")

# ══════════════════════════════════════════════════════════════════
#  YARDIMCILAR
# ══════════════════════════════════════════════════════════════════
