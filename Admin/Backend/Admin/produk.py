"""
F002-F004: CRUD Produk + Manajemen Stok + upload foto Cloudinary
"""
from flask import Blueprint, request, jsonify, g
from db_conn import query
from Backend.Utils.auth import auth_required, require_role
from Backend.Utils.cloudinary_util import upload_image, delete_image
from Backend.Utils.notify import create_notifikasi
from Backend.Utils.resend_util import send_stok_menipis_email

bp = Blueprint("produk", __name__, url_prefix="/api/produk")

THRESHOLD = 8
PREFIX_MAP = {"Kopi": "KP", "Non-Kopi": "NK", "Makanan": "MK", "Snack": "SN"}


def _next_kode(kategori):
    prefix = PREFIX_MAP.get(kategori, "PR")
    rows = query("SELECT kode FROM produk WHERE kode LIKE %s", (f"{prefix}-%",))
    nums = []
    for r in rows:
        try:
            nums.append(int(r["kode"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    nxt = (max(nums) if nums else 0) + 1
    return f"{prefix}-{nxt:03d}"


def _check_and_notify_stok(p):
    if p["stok"] == 0:
        create_notifikasi(
            target_role="admin", tipe="stok_habis", judul="Stok Habis",
            pesan=f"Stok \"{p['nama']}\" ({p['kode']}) telah habis.", ref_kode=p["kode"],
        )
        try:
            send_stok_menipis_email([p])
        except Exception:
            pass
    elif p["stok"] <= THRESHOLD:
        create_notifikasi(
            target_role="admin", tipe="stok_menipis", judul="Stok Menipis",
            pesan=f"Stok \"{p['nama']}\" ({p['kode']}) tersisa {p['stok']} unit.", ref_kode=p["kode"],
        )
        try:
            send_stok_menipis_email([p])
        except Exception:
            pass


@bp.get("")
@auth_required
def list_produk():
    rows = query("SELECT * FROM produk ORDER BY created_at DESC")
    return jsonify({"produk": rows})


@bp.post("")
@auth_required
@require_role("admin")
def add_produk():
    data = request.get_json(silent=True) or {}
    nama = (data.get("nama") or "").strip()
    kategori = data.get("kategori")
    harga = data.get("harga")
    stok = data.get("stok")
    status = data.get("status") or "Aktif"

    if not nama or not kategori or harga is None or stok is None:
        return jsonify({"message": "Nama, kategori, harga, dan stok wajib diisi."}), 400

    kode = _next_kode(kategori)
    query(
        "INSERT INTO produk (kode, nama, kategori, harga, stok, status) VALUES (%s,%s,%s,%s,%s,%s)",
        (kode, nama, kategori, harga, stok, status), fetch=None,
    )
    
    row = query("SELECT * FROM produk WHERE kode=%s", (kode,), fetch="one")
    return jsonify({"message": "Produk baru berhasil ditambahkan.", "produk": row}), 201


@bp.put("/<kode>")
@auth_required
@require_role("admin")
def update_produk(kode):
    data = request.get_json(silent=True) or {}
    query(
        "UPDATE produk SET nama=%s, kategori=%s, harga=%s, stok=%s, status=%s WHERE kode=%s",
        (data.get("nama"), data.get("kategori"), data.get("harga"), data.get("stok"), data.get("status"), kode),
        fetch=None,
    )
    row = query("SELECT * FROM produk WHERE kode=%s", (kode,), fetch="one")
    if not row:
        return jsonify({"message": "Produk tidak ditemukan."}), 404
    _check_and_notify_stok(row)
    return jsonify({"message": "Perubahan produk berhasil disimpan.", "produk": row})


@bp.delete("/<kode>")
@auth_required
@require_role("admin")
def delete_produk(kode):
    row = query("SELECT foto_public_id FROM produk WHERE kode=%s", (kode,), fetch="one")
    if row and row.get("foto_public_id"):
        delete_image(row["foto_public_id"])
    query("DELETE FROM produk WHERE kode=%s", (kode,), fetch=None)
    return jsonify({"message": "Produk berhasil dihapus."})


@bp.post("/<kode>/stok")
@auth_required
@require_role("admin")
def update_stok(kode):
    data = request.get_json(silent=True) or {}
    mode = data.get("mode")
    jumlah = data.get("jumlah")

    row = query("SELECT * FROM produk WHERE kode=%s", (kode,), fetch="one")
    if not row:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    try:
        jumlah = int(jumlah)
    except (TypeError, ValueError):
        return jsonify({"message": "Jumlah tidak valid."}), 400

    if mode == "tambah":
        baru = row["stok"] + jumlah
    elif mode == "kurangi":
        baru = max(0, row["stok"] - jumlah)
    elif mode == "set":
        baru = max(0, jumlah)
    else:
        return jsonify({"message": "Mode tidak dikenali."}), 400

    query("UPDATE produk SET stok=%s WHERE kode=%s", (baru, kode), fetch=None)
    updated = query("SELECT * FROM produk WHERE kode=%s", (kode,), fetch="one")
    _check_and_notify_stok(updated)
    return jsonify({"message": "Stok produk berhasil diperbarui.", "produk": updated})


@bp.post("/<kode>/foto")
@auth_required
@require_role("admin")
def upload_foto_produk(kode):
    if "foto" not in request.files:
        return jsonify({"message": "File foto tidak ditemukan."}), 400

    row = query("SELECT foto_public_id FROM produk WHERE kode=%s", (kode,), fetch="one")
    if row is None:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    try:
        result = upload_image(request.files["foto"], "antari/produk")
    except Exception as err:
        return jsonify({"message": f"Gagal mengunggah foto produk: {err}"}), 500

    if row.get("foto_public_id"):
        delete_image(row["foto_public_id"])

    query(
        "UPDATE produk SET foto_url=%s, foto_public_id=%s WHERE kode=%s",
        (result["url"], result["public_id"], kode), fetch=None,
    )
    return jsonify({"message": "Foto produk berhasil diperbarui.", "foto_url": result["url"]})
