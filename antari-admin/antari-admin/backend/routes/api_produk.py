"""
routes/api_produk.py
Endpoint API untuk modul "Manage Produk".

  GET    /api/produk          -> daftar semua produk (bisa difilter ?search=)
  GET    /api/produk/<id>     -> detail 1 produk
  POST   /api/produk          -> tambah produk baru (multipart/form-data, support foto)
  PUT    /api/produk/<id>     -> update produk
  DELETE /api/produk/<id>     -> hapus produk
"""

import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, current_app

from database import execute, query_all, query_one

bp = Blueprint("api_produk", __name__, url_prefix="/api/produk")

ALLOWED_EXT = {"jpg", "jpeg", "png"}


def _simpan_foto(file_storage):
    """Simpan file foto produk ke folder static/uploads, kembalikan path relatif."""
    if not file_storage or file_storage.filename == "":
        return None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return None

    nama_file = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = Path(current_app.static_folder) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_storage.save(upload_dir / nama_file)
    return f"uploads/{nama_file}"


@bp.get("")
def list_produk():
    search = request.args.get("search", "").strip()
    like = f"%{search}%"
    rows = query_all(
        "SELECT * FROM produk WHERE nama LIKE ? OR kode LIKE ? ORDER BY created_at DESC",
        (like, like),
    )
    return jsonify(rows)


@bp.get("/<int:produk_id>")
def get_produk(produk_id):
    row = query_one("SELECT * FROM produk WHERE id = ?", (produk_id,))
    if not row:
        return jsonify({"error": "Produk tidak ditemukan"}), 404
    return jsonify(row)


@bp.post("")
def create_produk():
    data = request.form
    kode = data.get("kode", "").strip()
    nama = data.get("nama", "").strip()

    if not kode or not nama:
        return jsonify({"error": "Kode Produk dan Nama Produk wajib diisi"}), 400

    if query_one("SELECT id FROM produk WHERE kode = ?", (kode,)):
        return jsonify({"error": f"Kode produk '{kode}' sudah digunakan"}), 400

    foto_path = _simpan_foto(request.files.get("foto"))

    produk_id = execute(
        """
        INSERT INTO produk (kode, nama, kategori, harga, stok, status, foto)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            kode,
            nama,
            data.get("kategori", ""),
            int(data.get("harga", 0) or 0),
            int(data.get("stok", 0) or 0),
            data.get("status", "tersedia"),
            foto_path,
        ),
    )
    return jsonify(query_one("SELECT * FROM produk WHERE id = ?", (produk_id,))), 201


@bp.put("/<int:produk_id>")
def update_produk(produk_id):
    if not query_one("SELECT id FROM produk WHERE id = ?", (produk_id,)):
        return jsonify({"error": "Produk tidak ditemukan"}), 404

    data = request.form if request.form else request.get_json(silent=True) or {}
    foto_path = None
    if request.files.get("foto"):
        foto_path = _simpan_foto(request.files.get("foto"))

    sql = """
        UPDATE produk SET nama=?, kategori=?, harga=?, stok=?, status=?
        {foto_clause} WHERE id=?
    """.format(foto_clause=", foto=?" if foto_path else "")

    params = [
        data.get("nama"),
        data.get("kategori"),
        int(data.get("harga", 0) or 0),
        int(data.get("stok", 0) or 0),
        data.get("status", "tersedia"),
    ]
    if foto_path:
        params.append(foto_path)
    params.append(produk_id)

    execute(sql, tuple(params))
    return jsonify(query_one("SELECT * FROM produk WHERE id = ?", (produk_id,)))


@bp.delete("/<int:produk_id>")
def delete_produk(produk_id):
    if not query_one("SELECT id FROM produk WHERE id = ?", (produk_id,)):
        return jsonify({"error": "Produk tidak ditemukan"}), 404
    execute("DELETE FROM produk WHERE id = ?", (produk_id,))
    return jsonify({"ok": True})
