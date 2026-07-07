"""
Seed awal database: akun admin & kasir (password di-hash dengan
bcrypt sebelum disimpan — password asli TIDAK PERNAH disimpan
mentah atau ditampilkan ke frontend), plus contoh produk & diskon.

Jalankan sekali dari root project:  python db/seed.py
Kredensial diambil dari .env (SEED_ADMIN_*, SEED_KASIR_*).
"""
import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt  # noqa: E402
from config import Config  # noqa: E402
from db_conn import query, test_connection  # noqa: E402
from app import create_app  # noqa: E402


def date_offset(days):
    return (date.today() + timedelta(days=days)).isoformat()


def upsert_user(username, password, nama, role, email):
    if not username or not password:
        print(f"[seed] Lewati akun {role}: username/password belum diisi di .env")
        return
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    existing = query("SELECT id FROM users WHERE username=%s", (username,), fetch="one")
    if existing:
        query(
            "UPDATE users SET password_hash=%s, nama=%s, role=%s, email=%s WHERE username=%s",
            (hashed, nama, role, email, username), fetch=None,
        )
        print(f'[seed] Akun "{username}" ({role}) diperbarui.')
    else:
        query(
            "INSERT INTO users (username, password_hash, nama, role, email) VALUES (%s,%s,%s,%s,%s)",
            (username, hashed, nama, role, email), fetch=None,
        )
        print(f'[seed] Akun "{username}" ({role}) dibuat.')


def seed_produk():
    count = query("SELECT COUNT(*) as c FROM produk", fetch="one")["c"]
    if count > 0:
        print("[seed] Produk sudah ada, lewati.")
        return

    produk = [
        ("KP-001", "Kopi Susu Gula Aren", "Kopi", 22000, 34),
        ("KP-002", "Americano", "Kopi", 18000, 40),
        ("KP-003", "Cappuccino", "Kopi", 25000, 28),
        ("KP-004", "Latte Vanilla", "Kopi", 26000, 22),
        ("KP-005", "Espresso Single Shot", "Kopi", 15000, 50),
        ("NK-001", "Matcha Latte", "Non-Kopi", 27000, 18),
        ("NK-002", "Chocolate Blend", "Non-Kopi", 24000, 20),
        ("NK-003", "Taro Milk", "Non-Kopi", 23000, 15),
        ("NK-004", "Lemon Tea", "Non-Kopi", 16000, 6),
        ("MK-001", "Croissant Butter", "Makanan", 19000, 12),
        ("MK-002", "Roti Bakar Coklat Keju", "Makanan", 21000, 14),
        ("MK-003", "Nasi Goreng Antari", "Makanan", 28000, 9),
        ("SN-001", "Kentang Goreng", "Snack", 17000, 25),
        ("SN-002", "Pisang Nugget", "Snack", 16000, 4),
        ("SN-003", "Cookies Cokelat", "Snack", 14000, 0),
    ]
    for kode, nama, kategori, harga, stok in produk:
        status = "Aktif" if stok > 0 else "Nonaktif"
        query(
            "INSERT INTO produk (kode, nama, kategori, harga, stok, status) VALUES (%s,%s,%s,%s,%s,%s)",
            (kode, nama, kategori, harga, stok, status), fetch=None,
        )
    print(f"[seed] {len(produk)} produk ditambahkan.")


def seed_diskon():
    count = query("SELECT COUNT(*) as c FROM diskon", fetch="one")["c"]
    if count > 0:
        print("[seed] Diskon sudah ada, lewati.")
        return

    diskon = [
        ("D-001", "Promo Jam Siang", "Persen", 10, date_offset(-5), date_offset(10), "Aktif"),
        ("D-002", "Diskon Member Antari", "Nominal", 5000, date_offset(-20), date_offset(40), "Aktif"),
        ("D-003", "Promo Ulang Tahun (berakhir)", "Persen", 15, date_offset(-60), date_offset(-30), "Nonaktif"),
    ]
    for d in diskon:
        query(
            "INSERT INTO diskon (id, nama, jenis, nilai, mulai, selesai, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            d, fetch=None,
        )
    print(f"[seed] {len(diskon)} diskon ditambahkan.")


def main():
    if not test_connection():
        sys.exit(1)

    upsert_user(
        os.getenv("SEED_ADMIN_USERNAME"), os.getenv("SEED_ADMIN_PASSWORD"),
        os.getenv("SEED_ADMIN_NAMA", "Admin Antari"), "admin", os.getenv("SEED_ADMIN_EMAIL"),
    )
    upsert_user(
        os.getenv("SEED_KASIR_USERNAME"), os.getenv("SEED_KASIR_PASSWORD"),
        os.getenv("SEED_KASIR_NAMA", "Kasir Antari"), "kasir", os.getenv("SEED_KASIR_EMAIL"),
    )

    seed_produk()
    seed_diskon()
    print("[seed] Selesai. Password TIDAK ditampilkan di sini — sudah tersimpan ter-hash.")


if __name__ == "__main__":
    flask_app = create_app()
    with flask_app.app_context():
        main()
