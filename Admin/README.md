# ANTARI Admin Flask

Project ini sudah dirapikan mengikuti pola struktur project portofolio Flask:

- `app.py` sebagai entry point utama.
- `Backend/` untuk route API Flask.
- `Frontend/Admin/` untuk halaman admin HTML, CSS, dan JavaScript.
- `db/` untuk schema TiDB/MySQL dan seed data awal.
- `vercel.json` untuk deploy ke Vercel.

Stack sesuai kebutuhan:

| Bagian | Teknologi |
|---|---|
| Bahasa | Python |
| Framework | Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | TiDB, kompatibel protokol MySQL |
| Upload image | Cloudinary |
| Email | Resend |
| Deploy | Vercel |

## Fitur Sesuai SRS Antari

| ID SRS | Fitur | Status |
|---|---|---|
| F001 | Login Sistem | Ada, memakai username, password hash bcrypt, dan JWT |
| F002 | Pengelolaan Produk | Ada, CRUD produk |
| F003 | Pengelolaan Stok | Ada, update stok dan alert stok menipis |
| F004 | Pengelolaan Kode Produk | Ada, kode otomatis per kategori |
| F005 | Pengelolaan Diskon | Ada, CRUD diskon |
| F006 | Penyimpanan Data Transaksi | Ada via API `/api/transaksi` |
| F007 | Riwayat Penjualan | Ada |
| F008 | Dashboard Penjualan | Ada |
| F009 | Pencarian Data | Ada di halaman frontend |
| F010 | Laporan Penjualan | Ada |
| F011 | Logout Sistem | Ada |

Catatan: UI project ini dibuat untuk admin. API transaksi tetap tersedia agar project kasir lain bisa disambungkan ke backend yang sama.

## Struktur Folder

```text
ANTARI_ADMIN_FLASK/
├── app.py
├── config.py
├── db_conn.py
├── wsgi.py
├── requirements.txt
├── vercel.json
├── .env.example
├── .gitignore
├── Backend/
│   ├── Admin/
│   │   ├── auth.py
│   │   ├── produk.py
│   │   ├── diskon.py
│   │   ├── transaksi.py
│   │   ├── laporan.py
│   │   ├── notifikasi.py
│   │   └── profil.py
│   └── Utils/
│       ├── auth.py
│       ├── cloudinary_util.py
│       ├── notify.py
│       └── resend_util.py
├── Frontend/
│   └── Admin/
│       ├── login.html
│       ├── dashboard.html
│       ├── produk.html
│       ├── diskon.html
│       ├── riwayat.html
│       ├── laporan.html
│       ├── profil.html
│       ├── css/style.css
│       └── js/
└── db/
    ├── schema.sql
    └── seed.py
```

## Cara Run Lokal

```bash
cd ANTARI_ADMIN_FLASK
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Isi `.env` dengan data TiDB, Cloudinary, Resend, dan akun awal.

Jalankan schema di TiDB Cloud SQL Editor atau lewat MySQL client:

```bash
mysql --ssl-mode=REQUIRED -h DB_HOST -P 3306 -u DB_USER -p antari_pos < db/schema.sql
```

Seed akun admin dan data contoh:

```bash
python db/seed.py
python app.py
```

Buka:

```text
http://localhost:4000/admin/login.html
```

## Endpoint Untuk Project Kasir

Project kasir lain bisa login dan menyimpan transaksi memakai API berikut:

| Kebutuhan | Method | Endpoint |
|---|---|---|
| Login kasir/admin | POST | `/api/auth/login` |
| Ambil produk | GET | `/api/produk` |
| Ambil diskon | GET | `/api/diskon` |
| Simpan transaksi | POST | `/api/transaksi` |
| Riwayat transaksi | GET | `/api/transaksi` |

Semua endpoint privat perlu header:

```text
Authorization: Bearer TOKEN_DARI_LOGIN
```

## Deploy Vercel

1. Upload semua isi folder ini ke GitHub.
2. Import repository ke Vercel.
3. Tambahkan Environment Variables di Vercel sesuai `.env.example`.
4. Pastikan TiDB memakai `DB_SSL=true`.
5. Deploy.

URL utama akan redirect ke:

```text
/admin/login.html
```
