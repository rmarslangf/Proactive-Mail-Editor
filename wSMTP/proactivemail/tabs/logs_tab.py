"""
tabs/logs_tab.py — Detaylı gönderim geçmişi.

Özellikler:
  - Kampanya seçimi
  - Durum filtresi (tümü / başarılı / başarısız)
  - Tablo: alıcı, email, durum, hata, tarih, tekrar dene sayısı
  - Seçili başarısızları tekrar gönder
  - CSV olarak dışa aktar
  - Kampanya özet (başarı oranı)
"""

import csv
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QFrame,
    QProgressBar
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QColor

from ..db import Database
from ..smtp_sender import SmtpSender, SmtpConfig, SendWorker


STYLE = """
QWidget { background:#16213e; color:#e8e4d9; }
QTableWidget { background:#0d1b2a; gridline-color:#1a3050;
               border:1px solid #1a3050; border-radius:6px; color:#e8e4d9; }
QTableWidget::item:selected { background:#e9456040; }
QHeaderView::section { background:#0f3460; color:#e8e4d9;
                        padding:6px; border:none; font-weight:700; }
QPushButton { background:#0f3460; color:#e8e4d9; border:none;
              border-radius:6px; padding:6px 14px; font-size:12px; }
QPushButton:hover { background:#e94560; }
QPushButton#retry { background:#1a3a5c; }
QPushButton#retry:hover { background:#e94560; }
QPushButton#export { background:#1a5c35; }
QPushButton#export:hover { background:#2ecc71; }
QComboBox { background:#0d1b2a; border:1px solid #0f3460;
            border-radius:6px; color:#e8e4d9; padding:5px 8px; }
QLabel#title { font-size:15px; font-weight:700; color:#e94560; }
QLabel#summary { font-size:12px; color:#7070a0; }
QProgressBar { border:1px solid #0f3460; border-radius:5px;
               background:#0d1b2a; text-align:center; }
QProgressBar::chunk { background:#e94560; border-radius:4px; }
"""


class LogsTab(QWidget):
    def __init__(self, db: Database, get_smtp_fn, get_html_fn,
                 get_subject_fn, parent=None):
        super().__init__(parent)
        self.db           = db
        self.get_smtp_cfg = get_smtp_fn
        self.get_html     = get_html_fn
        self.get_subject  = get_subject_fn
        self._worker: SendWorker = None
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        title = QLabel("📋  Gönderim Geçmişi")
        title.setObjectName("title")
        v.addWidget(title)

        # Filtre satırı
        top = QHBoxLayout()
        top.addWidget(QLabel("Kampanya:"))
        self.camp_cb = QComboBox()
        self.camp_cb.setMinimumWidth(280)
        self.camp_cb.currentIndexChanged.connect(self._load)
        top.addWidget(self.camp_cb)

        top.addWidget(QLabel("Durum:"))
        self.status_cb = QComboBox()
        self.status_cb.addItems(["Tümü", "Başarılı", "Başarısız"])
        self.status_cb.currentIndexChanged.connect(self._load)
        top.addWidget(self.status_cb)

        btn_refresh = QPushButton("🔄 Yenile")
        btn_refresh.clicked.connect(self.refresh)
        top.addWidget(btn_refresh)
        top.addStretch()

        btn_retry = QPushButton("🔁 Başarısızları Tekrar Gönder")
        btn_retry.setObjectName("retry")
        btn_retry.clicked.connect(self._retry_failed)
        top.addWidget(btn_retry)

        btn_exp = QPushButton("⬇ CSV İndir")
        btn_exp.setObjectName("export")
        btn_exp.clicked.connect(self._export_csv)
        top.addWidget(btn_exp)

        v.addLayout(top)

        # Özet
        self.summary_lbl = QLabel("")
        self.summary_lbl.setObjectName("summary")
        v.addWidget(self.summary_lbl)

        # Tekrar gönderim ilerleme
        self.retry_bar = QProgressBar()
        self.retry_bar.setVisible(False)
        v.addWidget(self.retry_bar)

        # Tablo
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Ad", "E-posta", "Durum", "Hata", "Tarih", "Tekrar"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnHidden(0, True)
        v.addWidget(self.table, 1)

    def refresh(self):
        # Kampanyaları yenile
        self.camp_cb.blockSignals(True)
        cur = self.camp_cb.currentText()
        self.camp_cb.clear()
        campaigns = self.db.get_campaigns()
        for c in campaigns:
            self.camp_cb.addItem(c)
        idx = self.camp_cb.findText(cur)
        if idx >= 0:
            self.camp_cb.setCurrentIndex(idx)
        self.camp_cb.blockSignals(False)
        self._load()

    def _load(self):
        campaign = self.camp_cb.currentText() or None
        st_idx   = self.status_cb.currentIndex()
        status   = {1: "sent", 2: "failed"}.get(st_idx)

        rows = self.db.get_logs(campaign=campaign, status=status)
        self._populate(rows)

        # Özet
        if campaign:
            s = self.db.get_log_summary(campaign)
            sent   = s.get("sent", 0)
            failed = s.get("failed", 0)
            total  = sent + failed
            rate   = int(sent / total * 100) if total else 0
            self.summary_lbl.setText(
                f"Toplam: {total}  |  ✅ {sent}  |  ❌ {failed}  |  Başarı: %{rate}"
            )
        else:
            self.summary_lbl.setText("")

    def _populate(self, rows):
        self.table.setRowCount(0)
        for ri, r in enumerate(rows):
            self.table.insertRow(ri)
            self.table.setItem(ri, 0, QTableWidgetItem(str(r["id"])))
            self.table.setItem(ri, 1, QTableWidgetItem(r["name"] or ""))
            self.table.setItem(ri, 2, QTableWidgetItem(r["email"]))

            st = r["status"]
            st_item = QTableWidgetItem(
                "✅ Gönderildi" if st == "sent" else
                "❌ Başarısız"  if st == "failed" else st
            )
            if st == "failed":
                st_item.setForeground(QColor("#e94560"))
            elif st == "sent":
                st_item.setForeground(QColor("#2ecc71"))
            self.table.setItem(ri, 3, st_item)
            self.table.setItem(ri, 4, QTableWidgetItem(r["error_msg"] or ""))
            self.table.setItem(ri, 5, QTableWidgetItem(r["sent_at"] or ""))
            self.table.setItem(ri, 6, QTableWidgetItem(str(r["retried"])))

    # ── Tekrar gönder ────────────────────────────────────────────────────────

    def _retry_failed(self):
        campaign = self.camp_cb.currentText()
        if not campaign:
            return

        failed = self.db.get_failed_for_campaign(campaign)
        if not failed:
            QMessageBox.information(self, "Tamam",
                "Bu kampanyada başarısız gönderim yok.")
            return

        cfg = self.get_smtp_cfg()
        if not cfg.user or not cfg.password:
            QMessageBox.warning(self, "SMTP", "SMTP ayarları eksik.")
            return

        html  = self.get_html()
        subj  = self.get_subject() or campaign.split(" [")[0]
        recipients = [{"id": r["recipient_id"], "name": r["name"],
                       "email": r["email"]} for r in failed]

        reply = QMessageBox.question(
            self, "Tekrar Gönder",
            f"{len(recipients)} başarısız alıcıya tekrar gönderilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.retry_bar.setMaximum(len(recipients))
        self.retry_bar.setValue(0)
        self.retry_bar.setVisible(True)
        self._retry_sent = self._retry_failed_cnt = 0

        from ..smtp_sender import SmtpSender, SendWorker
        sender = SmtpSender(cfg)
        self._worker = SendWorker(sender, recipients, subj, html, None)
        retry_camp = campaign + " [retry]"
        self._retry_camp = retry_camp
        self._retry_map  = {r["email"]: r for r in recipients}

        self._worker.progress.connect(self._on_retry_progress)
        self._worker.finished.connect(self._on_retry_done)
        self._worker.start()

    def _on_retry_progress(self, current, total, email, ok, err):
        self.retry_bar.setValue(current)
        rec = self._retry_map.get(email, {})
        rid = rec.get("id")
        name = rec.get("name", "")
        status = "sent" if ok else "failed"
        self.db.log_send(self._retry_camp, rid, email, name, status, err, retried=1)
        if ok:
            self._retry_sent += 1
        else:
            self._retry_failed_cnt += 1

    def _on_retry_done(self):
        self.retry_bar.setVisible(False)
        self.refresh()
        QMessageBox.information(
            self, "Tekrar Gönderim",
            f"✅ {self._retry_sent} başarılı\n❌ {self._retry_failed_cnt} başarısız"
        )

    # ── CSV dışa aktar ───────────────────────────────────────────────────────

    def _export_csv(self):
        campaign = self.camp_cb.currentText() or "log"
        safe = campaign.replace("/", "-").replace(":", "-")[:40]
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV Kaydet", f"{safe}.csv", "CSV (*.csv)")
        if not path:
            return
        rows = self.db.get_logs(campaign=self.camp_cb.currentText() or None)
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["ID","Ad","E-posta","Durum","Hata","Tarih","Tekrar"])
            for r in rows:
                writer.writerow([
                    r["id"], r["name"], r["email"],
                    r["status"], r["error_msg"],
                    r["sent_at"], r["retried"]
                ])
        QMessageBox.information(self, "Kaydedildi", f"CSV kaydedildi:\n{path}")
