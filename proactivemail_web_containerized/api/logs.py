"""
api/logs.py — Gönderim logları.

GET  /api/logs              — ?campaign=&status=&limit=
GET  /api/logs/campaigns    — kampanya listesi
GET  /api/logs/summary/<c>  — kampanya özeti
POST /api/logs/retry        — başarısızları tekrar gönder
"""

from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("logs", __name__)


def get_db():
    return current_app.config["DB"]


@bp.get("/logs")
def get_logs():
    db       = get_db()
    campaign = request.args.get("campaign")
    status   = request.args.get("status")
    limit    = request.args.get("limit", 500, type=int)
    rows     = db.get_logs(campaign=campaign, status=status, limit=limit)
    return jsonify([dict(r) for r in rows])


@bp.get("/logs/campaigns")
def get_campaigns():
    return jsonify(get_db().get_campaigns())


@bp.get("/logs/summary/<path:campaign>")
def get_summary(campaign):
    s = get_db().get_log_summary(campaign)
    total = sum(s.values())
    return jsonify({
        "summary": s,
        "total":   total,
        "rate":    round(s.get("sent", 0) / total * 100) if total else 0,
    })


@bp.post("/logs/retry")
def retry_failed():
    """Başarısız gönderimler için tekrar gönder isteği başlatır."""
    d        = request.json or {}
    campaign = d.get("campaign")
    if not campaign:
        return jsonify({"error": "campaign required"}), 400

    db     = current_app.config["DB"]
    failed = db.get_failed_for_campaign(campaign)
    if not failed:
        return jsonify({"error": "no failed records"}), 404

    # send/start endpoint'ine yönlendir
    from flask import url_for
    recipients = [{"id":    r["recipient_id"],
                   "name":  r["name"],
                   "email": r["email"]} for r in failed]
    return jsonify({
        "ok":         True,
        "count":      len(recipients),
        "recipients": recipients,
        "campaign":   campaign + " [retry]",
    })
