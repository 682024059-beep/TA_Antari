"""
seed.py
Mengisi database dengan data contoh yang meniru tampilan di Figma,
supaya begitu aplikasi pertama kali dijalankan, semua halaman langsung
terlihat berisi (tidak kosong).

Jalankan manual:
    python seed.py
Atau otomatis dipanggil oleh app.py saat database masih kosong.
"""

import random
from datetime import datetime, timedelta

from database import get_connection, init_db


PRODUK = [
    ("COF-001", "Aren Latte Ice", "Kopi", 28000, 120, "tersedia"),
    ("COF-002", "Cappuccino", "Kopi", 25000, 80, "tersedia"),
    ("COF-003", "Americano", "Kopi", 20000, 60, "tersedia"),
    ("COF-004", "Matcha Latte", "Non-Kopi", 27000, 45, "tersedia"),
    ("PST-001", "Butter Croissant", "Pastry", 18000, 30, "tersedia"),
    ("CKE-001", "Red Velvet Cake", "Cake", 32000, 0, "habis"),
    ("CKE-002", "Brownies", "Cake", 15000, 50, "tersedia"),
]

DISKON = [
    ("Promo Awal Tahun", "Semua Menu Kopi", "Persentase", 10, "01 Jan - 31 Jan", "AKTIF"),
    ("Diskon Member", "Menu Signature", "Nominal", 5000, "Selamanya", "AKTIF"),
    ("Flash Sale Malam", "Pastry & Cake", "Persentase", 30, "21:00 - 23:00", "DRAFT"),
]

CUSTOMERS = ["Andi Pratama", "Siti Aminah", "Guest #5", "Rudi Hartono",
             "Dewi Lestari", "Guest #2", "Bagus Saputra", "Nina Marlina"]
KASIR = ["Siska", "Budi", "Wulan"]
METODE = [("QRIS (Gopay)", False), ("Cash", True), ("Debit BCA", False), ("Cash", True)]
ITEM_POOL = [p[1] for p in PRODUK]


def seed():
    created = init_db(force=True)
    conn = get_connection()
    cur = conn.cursor()

    for kode, nama, kategori, harga, stok, status in PRODUK:
        cur.execute(
            "INSERT INTO produk (kode, nama, kategori, harga, stok, status) "
            "VALUES (?,?,?,?,?,?)",
            (kode, nama, kategori, harga, stok, status),
        )

    for nama, target, jenis, nilai, periode, status in DISKON:
        cur.execute(
            "INSERT INTO diskon (nama, produk_target, jenis, nilai, periode_label, status) "
            "VALUES (?,?,?,?,?,?)",
            (nama, target, jenis, nilai, periode, status),
        )

    # Buat ~120 transaksi contoh menyebar di 30 hari terakhir supaya
    # grafik "Pendapatan per Hari" dan statistik punya data yang masuk akal.
    no_counter = 89212
    today = datetime.now()
    for day_offset in range(30):
        tanggal = today - timedelta(days=day_offset)
        jumlah_transaksi_hari_ini = random.randint(2, 8)
        for _ in range(jumlah_transaksi_hari_ini):
            jam = random.randint(7, 21)
            menit = random.randint(0, 59)
            detik = random.randint(0, 59)
            waktu = tanggal.replace(hour=jam, minute=menit, second=detik)

            n_item = random.randint(1, 3)
            items = random.sample(ITEM_POOL, n_item)
            total = 0
            item_rows = []
            for nama_item in items:
                harga_item = next(p[3] for p in PRODUK if p[1] == nama_item)
                qty = random.randint(1, 2)
                total += harga_item * qty
                item_rows.append((nama_item, qty))

            metode, ada_diskon = random.choice(METODE)
            diskon_nominal = random.choice([0, 5000, 0, 0]) if ada_diskon else 0
            total = max(total - diskon_nominal, 0)

            no_transaksi = f"#TRX-{no_counter}"
            no_counter -= 1

            cur.execute(
                "INSERT INTO transaksi (no_transaksi, customer, total, diskon, metode, kasir, waktu) "
                "VALUES (?,?,?,?,?,?,?)",
                (
                    no_transaksi,
                    random.choice(CUSTOMERS),
                    total,
                    diskon_nominal,
                    metode,
                    random.choice(KASIR),
                    waktu.strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            transaksi_id = cur.lastrowid
            for nama_item, qty in item_rows:
                cur.execute(
                    "INSERT INTO transaksi_item (transaksi_id, nama_produk, qty) VALUES (?,?,?)",
                    (transaksi_id, nama_item, qty),
                )

    cur.execute("INSERT INTO settings (key, value) VALUES ('target_promo_bulanan', '5000000')")

    conn.commit()
    conn.close()
    print("Seed data berhasil dibuat." if created else "Database sudah ada, seed dibuat ulang (force).")


if __name__ == "__main__":
    seed()
