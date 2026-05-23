"""
api/send.py — Toplu gönderim endpoint'leri.

POST /api/send/start    — gönderimi başlat (arka planda thread)
GET  /api/send/progress — SSE stream (canlı ilerleme)
POST /api/send/stop     — durdur
GET  /api/send/status   — mevcut durum
"""

import threading
import queue
import json
import time
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context

from proactivemail.smtp_sender import SmtpSender, SmtpConfig, MODE_GMAIL, MODE_EXIM
from proactivemail.html_builder import build_html

bp = Blueprint("send", __name__)

# Global gönderim durumu (tek kullanıcı — basit)
_state = {
    "running":  False,
    "stop":     False,
    "progress": [],   # list of events
    "total":    0,
    "current":  0,
    "sent":     0,
    "failed":   0,
    "campaign": "",
}
_queue = queue.Queue()
_lock  = threading.Lock()


def get_db():
    return current_app.config["DB"]


def _get_smtp_config(db) -> SmtpConfig:
    s = db.get_all_settings()
    mode = s.get("smtp_mode", MODE_GMAIL)
    return SmtpConfig(
        mode        = mode,
        host        = s.get("smtp_host", "smtp.gmail.com"),
        port        = int(s.get("smtp_port", 587)),
        user        = s.get("smtp_user", ""),
        password    = s.get("smtp_password", ""),
        from_email  = s.get("smtp_from_email", ""),
        from_name   = s.get("smtp_from_name", ""),
        bounce_addr = s.get("smtp_bounce", ""),
        reply_to    = s.get("smtp_reply_to", ""),
        use_tls     = s.get("smtp_conn_type", "starttls") != "plain",
        delay_ms    = int(s.get("smtp_delay_ms", 200)),
        batch_size  = int(s.get("smtp_batch_size", 0)),
    )


def _send_thread(app, recipients, subject, html_body, campaign):
    """Arka planda çalışan gönderim thread'i."""
    with app.app_context():
        db     = app.config["DB"]
        cfg    = _get_smtp_config(db)
        sender = SmtpSender(cfg)
        total  = len(recipients)

        with _lock:
            _state["running"]  = True
            _state["stop"]     = False
            _state["total"]    = total
            _state["current"]  = 0
            _state["sent"]     = 0
            _state["failed"]   = 0
            _state["campaign"] = campaign
            _state["progress"] = []

        for i, r in enumerate(recipients, 1):
            with _lock:
                if _state["stop"]:
                    _queue.put({"type": "stopped"})
                    break

            ok, err = sender.send_one(
                r["email"], r.get("name", ""),
                subject, html_body
            )
            status = "sent" if ok else "failed"
            db.log_send(campaign, r.get("id"), r["email"],
                        r.get("name", ""), status, err)

            event = {
                "type":    "progress",
                "current": i,
                "total":   total,
                "email":   r["email"],
                "ok":      ok,
                "error":   err,
            }
            with _lock:
                _state["current"] = i
                _state["sent"]   += int(ok)
                _state["failed"] += int(not ok)
                _state["progress"].append(event)
            _queue.put(event)

            if cfg.delay_ms > 0:
                time.sleep(cfg.delay_ms / 1000.0)

        with _lock:
            _state["running"] = False
        _queue.put({"type": "done",
                    "sent": _state["sent"],
                    "failed": _state["failed"]})


@bp.post("/send/start")
def start_send():
    with _lock:
        if _state["running"]:
            return jsonify({"error": "already running"}), 409

    d          = request.json or {}
    subject    = d.get("subject", "ProactiveMail")
    blocks     = d.get("blocks", [])
    settings   = d.get("settings", {})
    group_id   = d.get("group_id")   # None = tümü
    test_mode  = d.get("test_mode", False)
    campaign   = d.get("campaign", subject)

    db = get_db()

    # HTML oluştur
    html = build_html(
        subject           = subject,
        blocks            = blocks,
        header_b64        = settings.get("header_b64") or None,
        header_bg         = settings.get("header_bg", "#1B3A5C"),
        header_text_color = settings.get("header_text_color", "#ffffff"),
        footer_b64        = settings.get("footer_b64") or None,
        footer_text       = settings.get("footer_text", ""),
        footer_bg         = settings.get("footer_bg", "#1B3A5C"),
        footer_text_color = settings.get("footer_text_color", "#AABCD0"),
        box_bg            = settings.get("box_bg", "#ffffff"),
        accent            = settings.get("accent", "#1B3A5C"),
        show_subject      = settings.get("show_subject", True),
        show_footer_text  = settings.get("show_footer_text", True),
        global_font_size  = settings.get("global_font_size", 15),
        global_font_family= settings.get("global_font_family", "Georgia, serif"),
    )

    if test_mode:
        cfg = _get_smtp_config(db)
        recipients = [{"id": None, "name": "Test",
                       "email": cfg.user or cfg.from_email}]
    else:
        rows = db.get_recipients(group_id=group_id)
        recipients = [{"id": r["id"], "name": r["name"],
                       "email": r["email"]} for r in rows]

    if not recipients:
        return jsonify({"error": "no recipients"}), 400

    # Queue temizle
    while not _queue.empty():
        _queue.get_nowait()

    app = current_app._get_current_object()
    t = threading.Thread(
        target=_send_thread,
        args=(app, recipients, subject, html, campaign),
        daemon=True
    )
    t.start()
    return jsonify({"ok": True, "total": len(recipients)})


@bp.get("/send/progress")
def send_progress():
    """Server-Sent Events — tarayıcıya canlı ilerleme gönder."""
    def event_stream():
        while True:
            try:
                event = _queue.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("done", "stopped"):
                    break
            except queue.Empty:
                yield "data: {\"type\":\"ping\"}\n\n"
    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@bp.post("/send/stop")
def stop_send():
    with _lock:
        _state["stop"] = True
    return jsonify({"ok": True})


@bp.get("/send/status")
def send_status():
    with _lock:
        return jsonify({k: v for k, v in _state.items() if k != "progress"})
