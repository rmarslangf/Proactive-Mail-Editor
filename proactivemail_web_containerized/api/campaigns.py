"""
api/campaigns.py — Kampanya taslakları.

GET    /api/campaigns          — liste
POST   /api/campaigns          — kaydet / güncelle
GET    /api/campaigns/<id>     — tek kampanya
DELETE /api/campaigns/<id>     — sil
POST   /api/campaigns/preview  — HTML önizleme üret (kaydetmeden)
"""

from flask import Blueprint, request, jsonify, current_app
from proactivemail.html_builder import build_html

bp = Blueprint("campaigns", __name__)


def get_db():
    return current_app.config["DB"]


@bp.get("/campaigns")
def list_campaigns():
    db   = get_db()
    rows = db.conn.execute(
        "SELECT * FROM campaigns ORDER BY updated_at DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@bp.post("/campaigns")
def save_campaign():
    d       = request.json or {}
    cid     = d.get("id")
    subject = d.get("subject", "").strip()
    blocks  = d.get("blocks", [])
    title   = d.get("title", subject or "Adsız")
    settings = d.get("settings", {})

    import json
    db = get_db()

    if cid:
        db.conn.execute(
            """UPDATE campaigns
               SET title=?, subject=?, blocks=?, settings=?, updated_at=datetime('now','localtime')
               WHERE id=?""",
            (title, subject, json.dumps(blocks, ensure_ascii=False),
             json.dumps(settings, ensure_ascii=False), cid)
        )
        db.conn.commit()
        return jsonify({"id": cid})
    else:
        cur = db.conn.execute(
            """INSERT INTO campaigns (title, subject, blocks, settings)
               VALUES (?, ?, ?, ?)""",
            (title, subject,
             json.dumps(blocks, ensure_ascii=False),
             json.dumps(settings, ensure_ascii=False))
        )
        db.conn.commit()
        return jsonify({"id": cur.lastrowid}), 201


@bp.get("/campaigns/<int:cid>")
def get_campaign(cid):
    db  = get_db()
    row = db.conn.execute(
        "SELECT * FROM campaigns WHERE id=?", (cid,)
    ).fetchone()
    if not row:
        return jsonify({"error": "not found"}), 404
    import json
    d = dict(row)
    d["blocks"]   = json.loads(d["blocks"] or "[]")
    d["settings"] = json.loads(d["settings"] or "{}")
    return jsonify(d)


@bp.delete("/campaigns/<int:cid>")
def delete_campaign(cid):
    db = get_db()
    db.conn.execute("DELETE FROM campaigns WHERE id=?", (cid,))
    db.conn.commit()
    return jsonify({"ok": True})


@bp.post("/campaigns/preview")
def preview():
    """HTML önizleme — kaydetmeden üret."""
    d        = request.json or {}
    subject  = d.get("subject", "ProactiveMail")
    blocks   = d.get("blocks", [])
    settings = d.get("settings", {})
    html = build_html(
        subject           = subject,
        blocks            = blocks,
        header_image_path = None,
        header_b64        = settings.get("header_b64") or None,
        header_bg         = settings.get("header_bg", "#1B3A5C"),
        header_text_color = settings.get("header_text_color", "#ffffff"),
        footer_text       = settings.get("footer_text", ""),
        footer_b64        = settings.get("footer_b64") or None,
        footer_bg         = settings.get("footer_bg", "#1B3A5C"),
        footer_text_color = settings.get("footer_text_color", "#AABCD0"),
        box_bg            = settings.get("box_bg", "#ffffff"),
        accent            = settings.get("accent", "#1B3A5C"),
        show_subject      = settings.get("show_subject", True),
        show_footer_text  = settings.get("show_footer_text", True),
        global_font_size  = settings.get("global_font_size", 15),
        global_font_family= settings.get("global_font_family", "Georgia, serif"),
    )
    return jsonify({"html": html})
