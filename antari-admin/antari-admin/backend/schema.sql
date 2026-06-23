-- Antari Admin - Coffee & Creamery
-- Database schema (SQLite)

DROP TABLE IF EXISTS transaksi_item;
DROP TABLE IF EXISTS transaksi;
DROP TABLE IF EXISTS diskon;
DROP TABLE IF EXISTS produk;
DROP TABLE IF EXISTS settings;

CREATE TABLE produk (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    kode        TEXT UNIQUE NOT NULL,
    nama        TEXT NOT NULL,
    kategori    TEXT,
    harga       INTEGER NOT NULL DEFAULT 0,
    stok        INTEGER NOT NULL DEFAULT 0,
    status      TEXT NOT NULL DEFAULT 'tersedia',   -- tersedia | habis
    foto        TEXT,                                -- relative path under /static/uploads
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE diskon (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nama            TEXT NOT NULL,
    produk_target   TEXT NOT NULL,                   -- e.g. "Semua Menu Kopi"
    jenis           TEXT NOT NULL,                    -- Persentase | Nominal
    nilai           INTEGER NOT NULL,                 -- percent (1-100) or rupiah amount
    periode_label   TEXT NOT NULL,                    -- e.g. "01 Jan - 31 Jan", "Selamanya"
    status          TEXT NOT NULL DEFAULT 'AKTIF',     -- AKTIF | DRAFT
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE transaksi (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    no_transaksi    TEXT UNIQUE NOT NULL,
    customer        TEXT NOT NULL,
    total           INTEGER NOT NULL DEFAULT 0,
    diskon          INTEGER NOT NULL DEFAULT 0,
    metode          TEXT NOT NULL,                     -- 'Cash', 'QRIS (Gopay)', 'Debit BCA', ...
    kasir           TEXT NOT NULL,
    waktu           TEXT NOT NULL                       -- ISO datetime, e.g. 2023-10-21 14:20:05
);

CREATE TABLE transaksi_item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    transaksi_id    INTEGER NOT NULL,
    nama_produk     TEXT NOT NULL,
    qty             INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (transaksi_id) REFERENCES transaksi(id) ON DELETE CASCADE
);

-- simple key/value settings table (e.g. target promo bulanan)
CREATE TABLE settings (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

CREATE INDEX idx_transaksi_waktu ON transaksi(waktu);
CREATE INDEX idx_item_transaksi ON transaksi_item(transaksi_id);
