"""
utils.py
Fungsi-fungsi bantu yang dipakai bersama oleh beberapa blueprint, terutama
untuk menghitung statistik penjualan (dipakai di Dashboard & Riwayat Penjualan).
"""

from datetime import datetime, timedelta

from database import query_all, query_one


def hitung_rentang_tanggal(range_key: str, start: str | None, end: str | None):
    """Mengembalikan (start_date, end_date) berformat 'YYYY-MM-DD'.

    Jika start & end dikirim manual (dari date-picker di UI), itu yang dipakai.
    Jika tidak, gunakan preset berdasarkan tab Harian / Mingguan / Bulanan.
    """
    today = datetime.now().date()

    if start and end:
        return start, end

    if range_key == "harian":
        return today.isoformat(), today.isoformat()
    if range_key == "mingguan":
        awal = today - timedelta(days=6)
        return awal.isoformat(), today.isoformat()

    # default: bulanan -> dari tanggal 1 bulan ini sampai hari ini
    awal_bulan = today.replace(day=1)
    return awal_bulan.isoformat(), today.isoformat()


def _rentang_sebelumnya(start_date: str, end_date: str):
    """Hitung rentang periode sebelumnya dengan durasi yang sama,
    dipakai untuk menghasilkan badge 'vs bulan lalu'."""
    d_start = datetime.fromisoformat(start_date).date()
    d_end = datetime.fromisoformat(end_date).date()
    durasi = (d_end - d_start).days + 1
    prev_end = d_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=durasi - 1)
    return prev_start.isoformat(), prev_end.isoformat()


def _persen_perubahan(sekarang: float, sebelumnya: float):
    if sebelumnya == 0:
        return 100.0 if sekarang > 0 else 0.0
    return round((sekarang - sebelumnya) / sebelumnya * 100, 1)


def ringkasan_penjualan(start_date: str, end_date: str):
    """Statistik kartu di atas: total transaksi, total pendapatan, metode cash/cashless."""

    def hitung(s, e):
        row = query_one(
            """
            SELECT
                COUNT(*) AS jumlah,
                COALESCE(SUM(total), 0) AS pendapatan,
                COALESCE(SUM(CASE WHEN metode = 'Cash' THEN total ELSE 0 END), 0) AS cash,
                COALESCE(SUM(CASE WHEN metode != 'Cash' THEN total ELSE 0 END), 0) AS cashless
            FROM transaksi
            WHERE date(waktu) BETWEEN ? AND ?
            """,
            (s, e),
        )
        return row

    sekarang = hitung(start_date, end_date)
    prev_start, prev_end = _rentang_sebelumnya(start_date, end_date)
    sebelumnya = hitung(prev_start, prev_end)

    return {
        "total_transaksi": sekarang["jumlah"],
        "total_pendapatan": sekarang["pendapatan"],
        "metode_cash": sekarang["cash"],
        "metode_cashless": sekarang["cashless"],
        "perubahan_transaksi": _persen_perubahan(sekarang["jumlah"], sebelumnya["jumlah"]),
        "perubahan_pendapatan": _persen_perubahan(sekarang["pendapatan"], sebelumnya["pendapatan"]),
    }


def grafik_pendapatan_harian(start_date: str, end_date: str):
    """Data untuk chart 'Pendapatan per Hari' -> list label tanggal + nominal."""
    rows = query_all(
        """
        SELECT date(waktu) AS tanggal, SUM(total) AS pendapatan
        FROM transaksi
        WHERE date(waktu) BETWEEN ? AND ?
        GROUP BY date(waktu)
        ORDER BY tanggal ASC
        """,
        (start_date, end_date),
    )
    data_per_tanggal = {r["tanggal"]: r["pendapatan"] for r in rows}

    d_start = datetime.fromisoformat(start_date).date()
    d_end = datetime.fromisoformat(end_date).date()

    labels, values = [], []
    hari = d_start
    hari_label_id = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    while hari <= d_end:
        labels.append(hari_label_id[hari.weekday()])
        values.append(data_per_tanggal.get(hari.isoformat(), 0))
        hari += timedelta(days=1)

    return {"labels": labels, "values": values}


def produk_terlaris(start_date: str, end_date: str, limit: int = 5):
    rows = query_all(
        """
        SELECT ti.nama_produk AS nama, SUM(ti.qty) AS qty
        FROM transaksi_item ti
        JOIN transaksi t ON t.id = ti.transaksi_id
        WHERE date(t.waktu) BETWEEN ? AND ?
        GROUP BY ti.nama_produk
        ORDER BY qty DESC
        LIMIT ?
        """,
        (start_date, end_date, limit),
    )
    total_qty = sum(r["qty"] for r in rows) or 1
    for r in rows:
        r["persen"] = round(r["qty"] / total_qty * 100)
    return rows


def daftar_transaksi(start_date, end_date, search, page, per_page):
    offset = (page - 1) * per_page
    like = f"%{search}%" if search else "%"

    rows = query_all(
        """
        SELECT id, no_transaksi, customer, total, diskon, metode, kasir, waktu
        FROM transaksi
        WHERE date(waktu) BETWEEN ? AND ? AND no_transaksi LIKE ?
        ORDER BY waktu DESC
        LIMIT ? OFFSET ?
        """,
        (start_date, end_date, like, per_page, offset),
    )
    total_row = query_one(
        "SELECT COUNT(*) AS n FROM transaksi WHERE date(waktu) BETWEEN ? AND ? AND no_transaksi LIKE ?",
        (start_date, end_date, like),
    )

    for r in rows:
        items = query_all(
            "SELECT nama_produk, qty FROM transaksi_item WHERE transaksi_id = ?",
            (r["id"],),
        )
        r["produk"] = ", ".join(f"{it['nama_produk']} ({it['qty']})" for it in items)

    return rows, total_row["n"]
