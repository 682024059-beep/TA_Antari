"""
routes/api_diskon.py
Endpoint API untuk modul "Manajemen Diskon".

  GET    /api/diskon          -> daftar semua diskon
  POST   /api/diskon          -> tambah diskon baru
  PUT    /api/diskon/<id>     -> update diskon
  DELETE /api/diskon/<id>     -> hapus diskon
  GET    /api/diskon/stats    -> data untuk 2 kartu statistik di bawah tabel
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from database import execute, query_all, query_one

bp = Blueprint("api_diskon", __name__, url_prefix="/api/diskon")


@bp.get("")
def list_diskon():
    rows = query_all("SELECT * FROM diskon ORDER BY created_at DESC")
    return jsonify(rows)


@bp.post("")
def create_diskon():
    data = request.get_json(force=True) or {}
    required = ["nama", "produk_target", "jenis", "nilai", "periode_label"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "Semua field wajib diisi"}), 400

    diskon_id = execute(
        """
        INSERT INTO diskon (nama, produk_target, jenis, nilai, periode_label, status)
        VALUES (?,?,?,?,?,?)
        """,
        (
            data["nama"],
            data["produk_target"],
            data["jenis"],
            int(data["nilai"]),
            data["periode_label"],
            data.get("status", "AKTIF"),
        ),
    )
    return jsonify(query_one("SELECT * FROM diskon WHERE id = ?", (diskon_id,))), 201


@bp.put("/<int:diskon_id>")
def update_diskon(diskon_id):
    if not query_one("SELECT id FROM diskon WHERE id = ?", (diskon_id,)):
        return jsonify({"error": "Diskon tidak ditemukan"}), 404

    data = request.get_json(force=True) or {}
    execute(
        """
        UPDATE diskon SET nama=?, produk_target=?, jenis=?, nilai=?, periode_label=?, status=?
        WHERE id=?
        """,
        (
            data.get("nama"),
            data.get("produk_target"),
            data.get("jenis"),
            int(data.get("nilai", 0)),
            data.get("periode_label"),
            data.get("status", "AKTIF"),
            diskon_id,
        ),
    )
    return jsonify(query_one("SELECT * FROM diskon WHERE id = ?", (diskon_id,)))


@bp.delete("/<int:diskon_id>")
def delete_diskon(diskon_id):
    if not query_one("SELECT id FROM diskon WHERE id = ?", (diskon_id,)):
        return jsonify({"error": "Diskon tidak ditemukan"}), 404
    execute("DELETE FROM diskon WHERE id = ?", (diskon_id,))
    return jsonify({"ok": True})


@bp.get("/stats")
def stats_diskon():
    """Data untuk kartu 'Total Diskon Digunakan' & 'Potongan Harga Berjalan'."""
    today = datetime.now().date()
    awal_bulan = today.replace(day=1)
    awal_bulan_lalu = (awal_bulan - timedelta(days=1)).replace(day=1)
    akhir_bulan_lalu = awal_bulan - timedelta(days=1)

    bulan_ini = query_one(
        """
        SELECT COUNT(*) AS jumlah, COALESCE(SUM(diskon), 0) AS total_potongan
        FROM transaksi WHERE diskon > 0 AND date(waktu) BETWEEN ? AND ?
        """,
        (awal_bulan.isoformat(), today.isoformat()),
    )
    bulan_lalu = query_one(
        """
        SELECT COUNT(*) AS jumlah FROM transaksi
        WHERE diskon > 0 AND date(waktu) BETWEEN ? AND ?
        """,
        (awal_bulan_lalu.isoformat(), akhir_bulan_lalu.isoformat()),
    )

    jumlah = bulan_ini["jumlah"]
    jumlah_lalu = bulan_lalu["jumlah"] or 0
    perubahan = round((jumlah - jumlah_lalu) / jumlah_lalu * 100, 1) if jumlah_lalu else 100.0

    target_row = query_one("SELECT value FROM settings WHERE key = 'target_promo_bulanan'")
    target = int(target_row["value"]) if target_row else 5000000
    pencapaian = min(round(bulan_ini["total_potongan"] / target * 100), 100) if target else 0

    return jsonify(
        {
            "total_diskon_digunakan": jumlah,
            "perubahan_persen": perubahan,
            "potongan_harga_berjalan": bulan_ini["total_potongan"],
            "target_promo": target,
            "pencapaian_persen": pencapaian,
        }
    )
