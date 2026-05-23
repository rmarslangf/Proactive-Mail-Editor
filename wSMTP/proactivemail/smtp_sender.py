"""
smtp_sender.py — SMTP / Exim bağlantısı ve toplu gönderim.

Modlar:
  MODE_GMAIL   — Gmail / uzak SMTP (TLS veya SSL, kimlik doğrulama zorunlu)
  MODE_EXIM    — Local Exim relay (auth yok, plain bağlantı, bounce adresi)

Sınıflar:
  SmtpConfig   — Bağlantı + gönderim ayarları
  SmtpSender   — Tek mail gönder, bağlantı testi
  SendWorker   — QThread tabanlı toplu gönderim
"""

import smtplib, ssl, time, socket, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr, formatdate, make_msgid
from dataclasses import dataclass
from typing import Optional, Tuple

from PyQt5.QtCore import QThread, pyqtSignal

MODE_GMAIL = "gmail"
MODE_EXIM  = "exim"


@dataclass
class SmtpConfig:
    # Bağlantı
    mode:          str   = MODE_GMAIL
    host:          str   = "smtp.gmail.com"
    port:          int   = 587
    # Kimlik (Gmail/uzak)
    user:          str   = ""
    password:      str   = ""
    use_tls:       bool  = True
    # Gönderen
    from_email:    str   = ""
    from_name:     str   = ""
    # Bounce / Return-Path
    bounce_addr:   str   = ""
    reply_to:      str   = ""
    # Hız
    delay_ms:      int   = 100
    batch_size:    int   = 0
    batch_pause_s: float = 2.0

    @property
    def sender_addr(self) -> str:
        return self.bounce_addr or self.from_email or self.user

    @property
    def from_header(self) -> str:
        addr = self.from_email or self.user
        return formataddr((self.from_name, addr)) if self.from_name else addr

    def is_exim(self) -> bool:
        return self.mode == MODE_EXIM


class SmtpSender:
    def __init__(self, config: SmtpConfig):
        self.cfg = config

    # ── Bağlantı testi ───────────────────────────────────────────────────────
    def test(self) -> Tuple[bool, str]:
        try:
            with self._connect() as s:
                pass
            mode = "Exim (local relay)" if self.cfg.is_exim() else "SMTP"
            return True, f"✅ {mode} bağlantısı başarılı → {self.cfg.host}:{self.cfg.port}"
        except smtplib.SMTPAuthenticationError:
            return False, "❌ Kimlik doğrulama hatası."
        except (smtplib.SMTPConnectError, ConnectionRefusedError, socket.gaierror) as e:
            return False, f"❌ Bağlantı kurulamadı: {e}"
        except Exception as e:
            return False, f"❌ {type(e).__name__}: {e}"

    # ── Tek mail gönder ──────────────────────────────────────────────────────
    def send_one(self, to_email: str, to_name: str,
                 subject: str, html_body: str,
                 header_image_path: Optional[str] = None) -> Tuple[bool, str]:
        try:
            msg = self._build_message(to_email, to_name, subject,
                                      html_body, header_image_path)
            with self._connect() as s:
                s.sendmail(self.cfg.sender_addr, [to_email], msg.as_string())
            return True, ""
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"Alıcı reddedildi: {e.recipients}"
        except smtplib.SMTPSenderRefused as e:
            return False, f"Gönderen reddedildi: {e.smtp_error}"
        except smtplib.SMTPDataError as e:
            return False, f"Veri hatası: {e.smtp_code} {e.smtp_error}"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    # ── SMTP bağlantısı aç ───────────────────────────────────────────────────
    def _connect(self) -> smtplib.SMTP:
        if self.cfg.is_exim():
            # Local Exim — auth yok
            s = smtplib.SMTP(self.cfg.host, self.cfg.port, timeout=30)
            s.ehlo_or_helo_if_needed()
            # Exim STARTTLS sunuyorsa dene ama zorlamıyoruz
            try:
                if s.has_extn("starttls"):
                    s.starttls(); s.ehlo()
            except Exception:
                pass
            return s

        # Gmail / uzak SMTP
        if self.cfg.use_tls:
            ctx = ssl.create_default_context()
            s = smtplib.SMTP(self.cfg.host, self.cfg.port, timeout=30)
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
        else:
            ctx = ssl.create_default_context()
            s = smtplib.SMTP_SSL(self.cfg.host, self.cfg.port,
                                  context=ctx, timeout=30)
        s.login(self.cfg.user, self.cfg.password)
        return s

    # ── Mesaj oluştur ────────────────────────────────────────────────────────
    def _build_message(self, to_email, to_name, subject,
                       html_body, header_image_path) -> MIMEMultipart:
        msg = MIMEMultipart("related")
        msg["From"]       = self.cfg.from_header
        msg["To"]         = formataddr((to_name, to_email)) if to_name else to_email
        msg["Subject"]    = subject
        msg["Date"]       = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid(domain=self._domain())

        if self.cfg.bounce_addr:
            msg["Return-Path"] = f"<{self.cfg.bounce_addr}>"
        if self.cfg.reply_to:
            msg["Reply-To"] = self.cfg.reply_to

        alt = MIMEMultipart("alternative")
        msg.attach(alt)
        alt.attach(MIMEText(html_body, "html", "utf-8"))

        if header_image_path and os.path.exists(header_image_path):
            with open(header_image_path, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", "<header_image>")
                img.add_header("Content-Disposition", "inline",
                               filename=os.path.basename(header_image_path))
                msg.attach(img)
        return msg

    def _domain(self) -> str:
        addr = self.from_email if hasattr(self, 'from_email') else (
            self.cfg.from_email or self.cfg.user)
        return addr.split("@")[-1] if "@" in addr else "localhost"


# ── Toplu gönderim QThread ───────────────────────────────────────────────────

class SendWorker(QThread):
    progress = pyqtSignal(int, int, str, bool, str)
    finished = pyqtSignal()
    stopped  = pyqtSignal()

    def __init__(self, sender: SmtpSender, recipients: list,
                 subject: str, html_body: str,
                 header_image_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.sender     = sender
        self.recipients = recipients
        self.subject    = subject
        self.html_body  = html_body
        self.header_img = header_image_path
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        cfg   = self.sender.cfg
        total = len(self.recipients)
        for i, r in enumerate(self.recipients, 1):
            if self._stop_flag:
                self.stopped.emit(); return
            ok, err = self.sender.send_one(
                r["email"], r.get("name",""),
                self.subject, self.html_body, self.header_img)
            self.progress.emit(i, total, r["email"], ok, err)
            if cfg.delay_ms > 0:
                time.sleep(cfg.delay_ms / 1000.0)
            if cfg.batch_size > 0 and i % cfg.batch_size == 0 and i < total:
                time.sleep(cfg.batch_pause_s)
        self.finished.emit()
