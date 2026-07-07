"""
Notifikasi (lonceng) — setiap user melihat notifikasi untuk role-nya
('admin'/'kasir') atau 'all'. Dibuat otomatis oleh sistem.
"""
from flask import Blueprint, jsonify, g
from db_conn import query
from Backend.Utils.auth import auth_required

bp = Blueprint("notifikasi", __name__, url_prefix="/api/notifikasi")


@bp.get("")
@auth_required
def list_notifikasi():
    role = g.user["role"]
    rows = query(
        """SELECT id, tipe, judul, pesan, ref_kode, is_read, created_at
           FROM notifikasi
           WHERE target_role=%s OR target_role='all'
           ORDER BY created_at DESC LIMIT 50""",
        (role,),
    )
    unread_row = query(
        "SELECT COUNT(*) as unread FROM notifikasi WHERE (target_role=%s OR target_role='all') AND is_read=0",
        (role,), fetch="one",
    )
    return jsonify({"notifikasi": rows, "unread": unread_row["unread"]})


@bp.post("/<int:notif_id>/baca")
@auth_required
def baca(notif_id):
    query("UPDATE notifikasi SET is_read=1 WHERE id=%s", (notif_id,), fetch=None)
    return jsonify({"message": "Notifikasi ditandai sudah dibaca."})


@bp.post("/baca-semua")
@auth_required
def baca_semua():
    query(
        "UPDATE notifikasi SET is_read=1 WHERE target_role=%s OR target_role='all'",
        (g.user["role"],), fetch=None,
    )
    return jsonify({"message": "Semua notifikasi ditandai sudah dibaca."})
