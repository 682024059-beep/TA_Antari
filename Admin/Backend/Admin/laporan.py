"""
Laporan Penjualan — agregasi dari tabel transaksi/transaksi_items
"""
from flask import Blueprint, request, jsonify
from db_conn import query
from Backend.Utils.auth import auth_required, require_role

bp = Blueprint("laporan", __name__, url_prefix="/api/laporan")


@bp.get("")
@auth_required
@require_role("admin")
def get_laporan():
    start = request.args.get("start")
    end = request.args.get("end")

    conds = []
    params = []
    if start:
        conds.append("t.tanggal >= %s")
        params.append(start)
    if end:
        conds.append("t.tanggal <= %s")
        params.append(end)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    summary = query(
        f"""SELECT COUNT(*) as jumlah_transaksi, COALESCE(SUM(total),0) as total_penjualan,
                   COALESCE(SUM(diskon_nominal),0) as total_diskon
            FROM transaksi t {where}""",
        params, fetch="one",
    )

    per_hari = query(
        f"""SELECT tanggal, COUNT(*) as jumlah_transaksi, SUM(total) as total
            FROM transaksi t {where} GROUP BY tanggal ORDER BY tanggal ASC""",
        params,
    )

    produk_terlaris = query(
        f"""SELECT ti.kode_produk, ti.nama, SUM(ti.qty) as qty_terjual, SUM(ti.subtotal) as total_omzet
            FROM transaksi_items ti
            JOIN transaksi t ON t.id = ti.transaksi_id
            {where}
            GROUP BY ti.kode_produk, ti.nama
            ORDER BY qty_terjual DESC
            LIMIT 10""",
        params,
    )

    metode_bayar = query(
        f"SELECT metode, COUNT(*) as jumlah, SUM(total) as total FROM transaksi t {where} GROUP BY metode",
        params,
    )

    return jsonify({
        "summary": summary, "perHari": per_hari,
        "produkTerlaris": produk_terlaris, "metodeBayar": metode_bayar,
    })
