"""
routes/api_penjualan.py
Endpoint API untuk modul "Riwayat Penjualan" (dan dipakai juga oleh Dashboard).

  GET /api/penjualan              -> ringkasan + grafik + produk terlaris + tabel transaksi (1 panggilan)
  GET /api/penjualan/export       -> unduh data transaksi sebagai file .xlsx
"""

import io
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from utils import (
    hitung_rentang_tanggal,
    ringkasan_penjualan,
    grafik_pendapatan_harian,
    produk_terlaris,
    daftar_transaksi,
)

bp = Blueprint("api_penjualan", __name__, url_prefix="/api/penjualan")


def _ambil_filter():
    range_key = request.args.get("range", "bulanan")
    start = request.args.get("start")
    end = request.args.get("end")
    return hitung_rentang_tanggal(range_key, start, end)


@bp.get("")
def get_penjualan():
    start_date, end_date = _ambil_filter()
    search = request.args.get("search", "").strip()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = int(request.args.get("per_page", 4))

    transaksi, total_row = daftar_transaksi(start_date, end_date, search, page, per_page)

    return jsonify(
        {
            "periode": {"start": start_date, "end": end_date},
            "ringkasan": ringkasan_penjualan(start_date, end_date),
            "grafik": grafik_pendapatan_harian(start_date, end_date),
            "produk_terlaris": produk_terlaris(start_date, end_date),
            "transaksi": transaksi,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_row,
                "total_pages": max((total_row + per_page - 1) // per_page, 1),
            },
        }
    )


@bp.get("/export")
def export_excel():
    """Ekspor daftar transaksi pada rentang tanggal terpilih ke file Excel (.xlsx)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font

    start_date, end_date = _ambil_filter()
    search = request.args.get("search", "").strip()
    transaksi, _ = daftar_transaksi(start_date, end_date, search, page=1, per_page=100000)

    wb = Workbook()
    ws = wb.active
    ws.title = "Riwayat Penjualan"

    header = ["No. Transaksi", "Customer", "Produk", "Total", "Diskon", "Metode", "Kasir", "Waktu"]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for t in transaksi:
        ws.append(
            [
                t["no_transaksi"],
                t["customer"],
                t["produk"],
                t["total"],
                t["diskon"],
                t["metode"],
                t["kasir"],
                t["waktu"],
            ]
        )

    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value is not None else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = max(12, max_len + 2)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    nama_file = f"riwayat-penjualan_{start_date}_{end_date}.xlsx"
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nama_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
