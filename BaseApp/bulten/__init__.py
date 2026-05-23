"""
bulten — Haber Bülteni Editörü paketi.

Modüller:
  config        — Platform, yollar, sabitler
  lang          — TR/EN dil paketleri
  style         — PyQt5 koyu tema stili
  utils         — Yardımcı fonksiyonlar (base64, renk btn)
  html_builder  — HTML şablon üreticisi
  block_widget  — BlockWidget (tek içerik bloğu)
  main_window   — MainWindow (ana uygulama penceresi)
"""
from .main_window import MainWindow
from .config import AUTO_SAVE_PATH
