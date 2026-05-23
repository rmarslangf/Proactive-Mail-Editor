"""
config.py — Platform tespiti, otomatik kayıt yolu, sabitler.
"""
import os, platform

PLATFORM = platform.system()  # "Windows" | "Darwin" | "Linux"

if PLATFORM == "Darwin":
    _CFG_DIR = os.path.expanduser("~/Library/Application Support/BultenEditor")
elif PLATFORM == "Linux":
    _CFG_DIR = os.path.expanduser("~/.config/BultenEditor")
else:
    _CFG_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(_CFG_DIR, exist_ok=True)
AUTO_SAVE_PATH = os.path.join(_CFG_DIR, "_last_project.json")

CORP_COLORS = [
    "#F5F7FA", "#EEF2F7", "#F0F4EE", "#FDF6EC",
    "#F4F0F8", "#EAF2FB", "#FAFAFA", "#E8EDF2",
]
CORP_NAMES_TR = ["Buz Beyazı","Gri Mavi","Soft Yeşil","Krem","Lavandar","Açık Mavi","Nötr Beyaz","Çelik Gri"]
CORP_NAMES_EN = ["Ice White","Blue Grey","Soft Green","Cream","Lavender","Light Blue","Neutral White","Steel Grey"]

FONT_LIST = [
    "Georgia, serif",
    "Arial, sans-serif",
    "Helvetica, sans-serif",
    "Times New Roman, serif",
    "Trebuchet MS, sans-serif",
    "Verdana, sans-serif",
    "Tahoma, sans-serif",
    "Courier New, monospace",
    "Palatino, serif",
]
