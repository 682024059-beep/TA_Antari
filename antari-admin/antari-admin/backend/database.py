"""
database.py
Lapisan koneksi database SQLite untuk Antari Admin.

Kenapa SQLite?
- Tidak perlu instalasi server database terpisah (cocok untuk belajar / prototipe).
- File database tunggal (antari.db) sehingga mudah dipindah/diback-up.
- Mudah diganti ke MySQL/PostgreSQL nanti karena query SQL yang dipakai standar.
"""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "antari.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection():
    """Buat koneksi baru ke database.

    row_factory = sqlite3.Row membuat hasil query bisa diakses seperti
    dictionary, misalnya row["nama"] selain row[1].
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force: bool = False):
    """Inisialisasi database dari schema.sql.

    force=True akan menghapus database lama dan membuat ulang dari nol
    (berguna saat development). Secara default hanya membuat database
    jika file belum ada.
    """
    if DB_PATH.exists() and not force:
        return False

    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    return True


def query_all(sql, params=()):
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def query_one(sql, params=()):
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def execute(sql, params=()):
    """Untuk INSERT/UPDATE/DELETE. Mengembalikan lastrowid."""
    conn = get_connection()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()
