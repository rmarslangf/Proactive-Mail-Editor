"""
api/recipients.py — Alıcı ve grup yönetimi REST API.

GET    /api/groups                  — grup listesi
POST   /api/groups                  — grup ekle
PUT    /api/groups/<id>             — grup güncelle
DELETE /api/groups/<id>             — grup sil

GET    /api/recipients              — alıcı listesi (?group_id=&subscribed=)
POST   /api/recipients              — alıcı ekle
PUT    /api/recipients/<id>         — alıcı güncelle
DELETE /api/recipients/<id>         — alıcı sil (soft)
POST   /api/recipients/<id>/unsub   — abonelik iptal
POST   /api/recipients/<id>/resub   — yeniden abone
POST   /api/recipients/import       — CSV içe aktar
"""

from flask import Blueprint, request, jsonify, current_app
import csv, io

bp = Blueprint("recipients", __name__)


def get_db():
    return current_app.config["DB"]


#Gruplar

@bp.get("/groups")
def list_groups():
    db = get_db()
    groups = db.get_groups()
    cnt = {g["id"]: db.get_recipient_count(g["id"]) for g in groups}
    return jsonify([{
        "id":    g["id"],
        "name":  g["name"],
        "color": g["color"],
        "count": cnt.get(g["id"], 0)
    } for g in groups])


@bp.post("/groups")
def add_group():
    data = request.json or {}
    name  = data.get("name", "").strip()
    color = data.get("color", "#1B3A5C")
    if not name:
        return jsonify({"error": "name required"}), 400
    try:
        gid = get_db().add_group(name, color)
        return jsonify({"id": gid, "name": name, "color": color}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 409


@bp.put("/groups/<int:gid>")
def update_group(gid):
    data  = request.json or {}
    name  = data.get("name", "").strip()
    color = data.get("color", "#1B3A5C")
    if not name:
        return jsonify({"error": "name required"}), 400
    get_db().update_group(gid, name, color)
    return jsonify({"ok": True})


@bp.delete("/groups/<int:gid>")
def delete_group(gid):
    get_db().delete_group(gid)
    return jsonify({"ok": True})


# Alıcılar

@bp.get("/recipients")
def list_recipients():
    db          = get_db()
    group_id    = request.args.get("group_id", type=int)
    sub_filter  = request.args.get("subscribed", "all")  # all | yes | no
    active_only = request.args.get("active", "1") == "1"

    rows = db.get_recipients(group_id=group_id,
                             active_only=active_only,
                             subscribed_only=False)
    if sub_filter == "yes":
        rows = [r for r in rows if r["subscribed"]]
    elif sub_filter == "no":
        rows = [r for r in rows if not r["subscribed"]]

    return jsonify([{
        "id":         r["id"],
        "name":       r["name"],
        "email":      r["email"],
        "company":    r["company"],
        "group_id":   r["group_id"],
        "group_name": r["group_name"],
        "group_color":r["group_color"],
        "active":     bool(r["active"]),
        "subscribed": bool(r["subscribed"]),
        "notes":      r["notes"],
        "created_at": r["created_at"],
    } for r in rows])


@bp.post("/recipients")
def add_recipient():
    d = request.json or {}
    email = d.get("email", "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "valid email required"}), 400
    try:
        rid = get_db().add_recipient(
            d.get("name", ""), email,
            d.get("company", ""),
            d.get("group_id"),
            d.get("notes", "")
        )
        return jsonify({"id": rid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 409


@bp.put("/recipients/<int:rid>")
def update_recipient(rid):
    d = request.json or {}
    get_db().update_recipient(
        rid,
        d.get("name", ""),
        d.get("email", "").strip().lower(),
        d.get("company", ""),
        d.get("group_id"),
        d.get("notes", ""),
        int(d.get("active", 1)),
        int(d.get("subscribed", 1))
    )
    return jsonify({"ok": True})


@bp.delete("/recipients/<int:rid>")
def delete_recipient(rid):
    get_db().delete_recipient(rid)
    return jsonify({"ok": True})


@bp.post("/recipients/<int:rid>/unsub")
def unsub(rid):
    get_db().unsubscribe(rid)
    return jsonify({"ok": True})


@bp.post("/recipients/<int:rid>/resub")
def resub(rid):
    get_db().resubscribe(rid)
    return jsonify({"ok": True})


@bp.post("/recipients/import")
def import_csv():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f        = request.files["file"]
    group_id = request.form.get("group_id", type=int)
    content  = f.read().decode("utf-8-sig")
    # TMP to StringIO
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                     delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        result = get_db().import_csv(tmp_path, group_id)
    finally:
        os.unlink(tmp_path)
    return jsonify(result)
