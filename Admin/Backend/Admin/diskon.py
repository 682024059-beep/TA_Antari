"""
F005: CRUD Diskon
"""
from flask import Blueprint, request, jsonify
from db_conn import query
from Backend.Utils.auth import auth_required, require_role
from Backend.Utils.notify import create_notifikasi

bp = Blueprint("diskon", __name__, url_prefix="/api/diskon")


def _next_id():
    rows = query("SELECT id FROM diskon")
    nums = []
    for r in rows:
        try:
            nums.append(int(str(r["id"]).split("-")[1]))
        except (IndexError, ValueError):
            pass
    nxt = (max(nums) if nums else 0) + 1
    return f"D-{nxt:03d}"


@bp.get("")
@auth_required
def list_diskon():
    rows = query("SELECT * FROM diskon ORDER BY created_at DESC")
    return jsonify({"diskon": rows})


@bp.post("")
@auth_required
@require_role("admin")
def add_diskon():
    data = request.get_json(silent=True) or {}
    nama = (data.get("nama") or "").strip()
    jenis = data.get("jenis")
    nilai = data.get("nilai")
    mulai = data.get("mulai")
    selesai = data.get("selesai")
    status = data.get("status") or "Aktif"

    if not nama or not jenis or nilai is None or not mulai or not selesai:
        return jsonify({"message": "Semua field diskon wajib diisi."}), 400

    diskon_id = _next_id()
    query(
        "INSERT INTO diskon (id, nama, jenis, nilai, mulai, selesai, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (diskon_id, nama, jenis, nilai, mulai, selesai, status), fetch=None,
    )
    create_notifikasi(
        target_role="all", tipe="diskon", judul="Diskon Baru",
        pesan=f'Diskon "{nama}" telah dibuat dan aktif mulai {mulai}.', ref_kode=diskon_id,
    )
    row = query("SELECT * FROM diskon WHERE id=%s", (diskon_id,), fetch="one")
    return jsonify({"message": "Diskon baru berhasil ditambahkan.", "diskon": row}), 201


@bp.put("/<diskon_id>")
@auth_required
@require_role("admin")
def update_diskon(diskon_id):
    data = request.get_json(silent=True) or {}
    query(
        "UPDATE diskon SET nama=%s, jenis=%s, nilai=%s, mulai=%s, selesai=%s, status=%s WHERE id=%s",
        (data.get("nama"), data.get("jenis"), data.get("nilai"), data.get("mulai"),
         data.get("selesai"), data.get("status"), diskon_id),
        fetch=None,
    )
    row = query("SELECT * FROM diskon WHERE id=%s", (diskon_id,), fetch="one")
    if not row:
        return jsonify({"message": "Diskon tidak ditemukan."}), 404
    return jsonify({"message": "Perubahan diskon berhasil disimpan.", "diskon": row})


@bp.delete("/<diskon_id>")
@auth_required
@require_role("admin")
def delete_diskon(diskon_id):
    query("DELETE FROM diskon WHERE id=%s", (diskon_id,), fetch=None)
    return jsonify({"message": "Diskon berhasil dihapus."})
