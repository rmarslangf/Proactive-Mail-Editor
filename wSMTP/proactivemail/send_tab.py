"""
tabs/send_tab.py — Campaign gönderim sekmesi.

Özellikler:
  - Grup / tüm alıcı seçimi
  - Test modu (sadece SMTP kullanıcısına gönder)
  - İlerleme çubuğu + canlı log
  - Durdur butonu
  - Gönderim tamamlanınca özet
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QProgressBar, QTextEdit,
    QCheckBox, QGroupBox, QMessageBox, QSizePolicy,
    QFrame
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QColor

from ..db import Database
from ..smtp_sender import SmtpSender, SmtpConfig, SendWorker
from ..html_builder import build_html


STYLE = """
QWidget { background:#16213e; color:#e8e4d9; }
QGroupBox { border:1px solid #0f3460; border-radius:8px;
            margin-top:12px; padding:12px 10px 8px;
            font-size:11px; font-weight:700; color:#5a5a8a; }
QGroupBox::title { subcontrol-origin:margin; left:12px;
                   padding:0 6px; background:#16213e; }
QPushButton { background:#0f3460; color:#e8e4d9; border:none;
              border-radius:6px; padding:8px 18px; font-size:13px; }
QPushButton:hover { background:#e94560; }
QPushButton#go { background:#27ae60; font-size:14px; font-weight:700;
                 padding:10px 28px; }
QPushButton#go:hover { background:#2ecc71; }
QPushButton#stop { background:#7b1a1a; }
QPushButton#stop:hover { background:#e94560; }
QPushButton:disabled { background:#1a2535; color:#3a4a5a; }
QComboBox { background:#0d1b2a; border:1px solid #0f3460;
            border-radius:6px; color:#e8e4d9; padding:6px 10px; }
QProgressBar { border:1px solid #0f3460; border-radius:6px;
               background:#0d1b2a; color:#e8e4d9; text-align:center; }
QProgressBar::chunk { background:#27ae60; border-radius:5px; }
QTextEdit { background:#0d1b2a; border:1px solid #1a3050;
            border-radius:6px; color:#ccc; font-family:monospace;
            font-size:12px; }
QLabel#title { font-size:16px; font-weight:700; color:#e94560; }
QLabel#stat  { font-size:12px; color:#7070a0; }
QCheckBox { color:#a0a0c0; }
"""


class SendTab(QWidget):
    def __init__(self, db: Database, get_html_fn, get_subject_fn,
                 get_smtp_fn, parent=None):
        """
        get_html_fn    : () → str    — mevcut campaign HTML'ini döndürür
        get_subject_fn : () → str    — konu satırı
        get_smtp_fn    : () → SmtpConfig
        """
        super().__init__(parent)
        self.db           = db
        self.get_html     = get_html_fn
        self.get_subject  = get_subject_fn
        self.get_smtp_cfg = get_smtp_fn
        self._worker: SendWorker = None
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        title = QLabel("🚀  Campaign Gönder")
        title.setObjectName("title")
        v.addWidget(title)

        # ── Ayarlar
        cfg_box = QGroupBox("GÖNDERİM AYARLARI")
        cf = QVBoxLayout(cfg_box)
        cf.setSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Alıcı Grubu:"))
        self.group_cb = QComboBox()
        row1.addWidget(self.group_cb, 1)
        cf.addLayout(row1)

        row2 = QHBoxLayout()
        self.test_chk = QCheckBox(
            "Test modu — sadece SMTP hesabıma gönder")
        row2.addWidget(self.test_chk)
        row2.addStretch()
        cf.addLayout(row2)

        row3 = QHBoxLayout()
        self.count_lbl = QLabel("0 alıcı seçili")
        self.count_lbl.setObjectName("stat")
        row3.addWidget(self.count_lbl)
        row3.addStretch()
        cf.addLayout(row3)

        v.addWidget(cfg_box)

        # ── Gönder / Durdur butonları
        btn_row = QHBoxLayout()
        self.btn_send = QPushButton("🚀  Gönderimi Başlat")
        self.btn_send.setObjectName("go")
        self.btn_send.clicked.connect(self.start_send)
        self.btn_stop = QPushButton("⏹  Durdur")
        self.btn_stop.setObjectName("stop")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_send)
        btn_row.addWidget(self.btn_send)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        v.addLayout(btn_row)

        # ── İlerleme
        self.progress = QProgressBar()
        self.progress.setValue(0)
        v.addWidget(self.progress)

        # ── Stat satırı
        stat_row = QHBoxLayout()
        self.sent_lbl  = QLabel("✅ 0")
        self.fail_lbl  = QLabel("❌ 0")
        self.skip_lbl  = QLabel("⏭ 0")
        for l in [self.sent_lbl, self.fail_lbl, self.skip_lbl]:
            l.setObjectName("stat")
            stat_row.addWidget(l)
        stat_row.addStretch()
        v.addLayout(stat_row)

        # ── Canlı log
        v.addWidget(QLabel("Gönderim Logu:"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        v.addWidget(self.log_view, 1)

        # Grup combo'yu doldur
        self.refresh_groups()

    # ── Grup combo ───────────────────────────────────────────────────────────

    def refresh_groups(self):
        self.group_cb.clear()
        self.group_cb.addItem("Tüm aktif & abone alıcılar", None)
        for g in self.db.get_groups():
            cnt = self.db.get_recipient_count(g["id"])
            self.group_cb.addItem(f"{g['name']}  ({cnt})", g["id"])
        self.group_cb.currentIndexChanged.connect(self._update_count)
        self._update_count()

    def _update_count(self):
        gid = self.group_cb.currentData()
        cnt = self.db.get_recipient_count(gid)
        self.count_lbl.setText(f"{cnt} alıcı seçili")

    # ── Gönderim ─────────────────────────────────────────────────────────────

    def start_send(self):
        cfg = self.get_smtp_cfg()
        if not cfg.user or not cfg.password:
            QMessageBox.warning(self, "SMTP",
                "SMTP ayarları eksik. ⚙️ Ayarlar sekmesini kontrol edin.")
            return

        html  = self.get_html()
        subj  = self.get_subject() or "ProactiveMail"

        if self.test_chk.isChecked():
            recipients = [{"id": None, "name": "Test", "email": cfg.user}]
        else:
            gid = self.group_cb.currentData()
            rows = self.db.get_recipients(group_id=gid)
            recipients = [{"id": r["id"], "name": r["name"],
                           "email": r["email"]} for r in rows]

        if not recipients:
            QMessageBox.information(self, "Boş", "Gönderilecek alıcı yok.")
            return

        reply = QMessageBox.question(
            self, "Onay",
            f"{len(recipients)} alıcıya '{subj}' campaigni gönderilsin mi?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self._sent = self._failed = 0
        self.log_view.clear()
        self.progress.setMaximum(len(recipients))
        self.progress.setValue(0)
        self._update_stats()
        self.btn_send.setEnabled(False)
        self.btn_stop.setEnabled(True)

        sender = SmtpSender(cfg)
        self._worker = SendWorker(
            sender, recipients, subj, html,
            header_image_path=None  # HTML'e base64 embed edildi
        )
        self._campaign = f"{subj} [{QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm')}]"
        self._recipients_map = {r["email"]: r for r in recipients}

        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.stopped.connect(self._on_stopped)
        self._worker.start()

    def stop_send(self):
        if self._worker:
            self._worker.stop()
        self.btn_stop.setEnabled(False)

    def _on_progress(self, current, total, email, ok, err):
        self.progress.setValue(current)
        rec = self._recipients_map.get(email, {})
        rid = rec.get("id")
        name = rec.get("name", "")

        if ok:
            self._sent += 1
            self.db.log_send(self._campaign, rid, email, name, "sent")
            self._log(f"✅ {email}", "#2ecc71")
        else:
            self._failed += 1
            self.db.log_send(self._campaign, rid, email, name, "failed", err)
            self._log(f"❌ {email}  — {err}", "#e94560")

        self._update_stats()

    def _on_finished(self):
        self._done()
        QMessageBox.information(
            self, "Tamamlandı",
            f"Gönderim tamamlandı!\n\n"
            f"✅ Başarılı: {self._sent}\n"
            f"❌ Başarısız: {self._failed}"
        )

    def _on_stopped(self):
        self._done()
        self._log("⏹ Gönderim durduruldu.", "#e9a000")

    def _done(self):
        self.btn_send.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _log(self, msg, color="#ccc"):
        ts = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.log_view.append(
            f'<span style="color:#5a5a8a;">[{ts}]</span> '
            f'<span style="color:{color};">{msg}</span>'
        )

    def _update_stats(self):
        self.sent_lbl.setText(f"✅ {self._sent}")
        self.fail_lbl.setText(f"❌ {self._failed}")
