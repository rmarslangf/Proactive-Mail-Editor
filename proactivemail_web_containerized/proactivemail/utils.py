"""
utils.py — Genel yardımcı fonksiyonlar.
"""
import base64, mimetypes
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog

def img_to_b64(path):
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{b64}"

def make_color_btn(color_hex, on_change):
    btn = QPushButton()
    btn._hex = color_hex
    btn._cb  = on_change
    _apply_color_btn_style(btn, color_hex)
    def _click():
        c = QColorDialog.getColor(QColor(btn._hex), None, "")
        if c.isValid():
            btn._hex = c.name()
            _apply_color_btn_style(btn, btn._hex)
            btn._cb(btn._hex)
    btn.clicked.connect(_click)
    return btn

def _apply_color_btn_style(btn, hex_color):
    btn.setFixedSize(28, 28)
    btn.setStyleSheet(
        f"QPushButton{{background:{hex_color};border:2px solid #0f3460;"
        f"border-radius:6px;}}"
        f"QPushButton:hover{{border-color:#e94560;}}"
    )
    btn._hex = hex_color

def set_color_btn(btn, hex_color):
    _apply_color_btn_style(btn, hex_color)

