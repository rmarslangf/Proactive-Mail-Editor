"""
bulten — ProactiveMail (SMTP + SQLite versiyonu)

Modüller:
  config        — Platform, yollar, sabitler
  lang          — TR/EN dil paketleri
  style         — PyQt5 koyu tema
  utils         — Yardımcı fonksiyonlar
  html_builder  — HTML şablon üreticisi
  block_widget  — İçerik bloğu widget'ı
  main_window   — Ana pencere (editör + SMTP sekmeleri)
  db            — SQLite veritabanı (alıcılar, gruplar, log)
  smtp_sender   — SMTP gönderici + QThread worker
  tabs/
    recipients_tab — Alıcı & grup yönetimi
    send_tab       — Toplu gönderim
    logs_tab       — Gönderim geçmişi & tekrar dene
"""
from .main_window import MainWindow
from .config import AUTO_SAVE_PATH
from .db import Database
