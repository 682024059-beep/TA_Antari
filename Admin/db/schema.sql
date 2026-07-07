-- ============================================================
-- ANTARI Admin — Skema database TiDB/MySQL
-- Jalankan di TiDB Cloud SQL Editor atau via mysql client:
-- mysql --ssl-mode=REQUIRED -h HOST -P 3306 -u USER -p antari_pos < db/schema.sql
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nama          VARCHAR(120) NOT NULL,
  role          ENUM('admin','kasir') NOT NULL DEFAULT 'kasir',
  email         VARCHAR(150) NULL,
  foto_url      VARCHAR(500) NULL,
  is_active     TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS produk (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  kode        VARCHAR(20)  NOT NULL UNIQUE,
  nama        VARCHAR(150) NOT NULL,
  kategori    ENUM('Kopi','Non-Kopi','Makanan','Snack') NOT NULL,
  harga       INT NOT NULL DEFAULT 0,
  stok        INT NOT NULL DEFAULT 0,
  status      ENUM('Aktif','Nonaktif') NOT NULL DEFAULT 'Aktif',
  foto_url    VARCHAR(500) NULL,
  foto_public_id VARCHAR(255) NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS diskon (
  id          VARCHAR(20) PRIMARY KEY,
  nama        VARCHAR(150) NOT NULL,
  jenis       ENUM('Persen','Nominal') NOT NULL,
  nilai       INT NOT NULL,
  mulai       DATE NOT NULL,
  selesai     DATE NOT NULL,
  status      ENUM('Aktif','Nonaktif') NOT NULL DEFAULT 'Aktif',
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS transaksi (
  id              VARCHAR(20) PRIMARY KEY,
  tanggal         DATE NOT NULL,
  waktu           VARCHAR(10) NOT NULL,
  subtotal        INT NOT NULL DEFAULT 0,
  diskon_nominal  INT NOT NULL DEFAULT 0,
  diskon_id       VARCHAR(20) NULL,
  total           INT NOT NULL DEFAULT 0,
  metode          ENUM('Tunai','QRIS') NOT NULL DEFAULT 'Tunai',
  kasir_username  VARCHAR(50) NOT NULL,
  nama_customer   VARCHAR(150) NULL,
  email_customer  VARCHAR(150) NULL,
  struk_terkirim  TINYINT(1) NOT NULL DEFAULT 0,
  created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (diskon_id) REFERENCES diskon(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS transaksi_items (
  id            BIGINT AUTO_INCREMENT PRIMARY KEY,
  transaksi_id  VARCHAR(20) NOT NULL,
  kode_produk   VARCHAR(20) NOT NULL,
  nama          VARCHAR(150) NOT NULL,
  harga         INT NOT NULL,
  qty           INT NOT NULL,
  subtotal      INT NOT NULL,
  FOREIGN KEY (transaksi_id) REFERENCES transaksi(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS notifikasi (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  target_role ENUM('admin','kasir','all') NOT NULL DEFAULT 'admin',
  tipe        ENUM('stok_menipis','stok_habis','transaksi_baru','diskon','sistem') NOT NULL DEFAULT 'sistem',
  judul       VARCHAR(150) NOT NULL,
  pesan       VARCHAR(500) NOT NULL,
  ref_kode    VARCHAR(30) NULL,
  is_read     TINYINT(1) NOT NULL DEFAULT 0,
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_transaksi_tanggal ON transaksi(tanggal);
CREATE INDEX idx_notifikasi_role_read ON notifikasi(target_role, is_read);
