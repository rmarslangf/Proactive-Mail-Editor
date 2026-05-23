"""
api/settings.py — SMTP ayarları.

GET  /api/settings        — tüm ayarları getir
POST /api/settings        — kaydet
POST /api/settings/test   — SMTP bağlantı testi
"""

from flask import Blueprint, request, jsonify, current_app
from proactivemail.smtp_sender import SmtpSender, SmtpConfig, MODE_GMAIL, MODE_EXIM

bp = Blueprint("settings", __name__)


def get_db():
    return current_app.config["DB"]


@bp.get("/settings")
def get_settings():
    s = get_db().get_all_settings()
    # Şifreyi maskele
    masked = dict(s)
    if "smtp_password" in masked and masked["smtp_password"]:
        masked["smtp_password"] = "••••••••"
    return jsonify(masked)


@bp.post("/settings")
def save_settings():
    d  = request.json or {}
    db = get_db()
    # Şifre boş gelirse mevcut değeri koru
    if "smtp_password" in d and d["smtp_password"].startswith("•"):
        d.pop("smtp_password")
    db.save_settings(d)
    return jsonify({"ok": True})


@bp.post("/settings/test")
def test_smtp():
    db  = get_db()
    s   = db.get_all_settings()
    d   = request.json or {}
    # İstekten gelen değerler DB'den önce gelir
    s.update({k: v for k, v in d.items() if v})

    mode = s.get("smtp_mode", MODE_GMAIL)
    cfg  = SmtpConfig(
        mode        = mode,
        host        = s.get("smtp_host", "smtp.gmail.com"),
        port        = int(s.get("smtp_port", 587)),
        user        = s.get("smtp_user", ""),
        password    = s.get("smtp_password", ""),
        from_email  = s.get("smtp_from_email", ""),
        from_name   = s.get("smtp_from_name", ""),
        bounce_addr = s.get("smtp_bounce", ""),
        use_tls     = s.get("smtp_conn_type", "starttls") != "plain",
    )
    ok, msg = SmtpSender(cfg).test()
    return jsonify({"ok": ok, "message": msg})
