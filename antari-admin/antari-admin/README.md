# Antari Admin — Coffee & Creamery

Aplikasi dashboard admin kasir, dibuat berdasarkan desain Figma yang dibagikan
(Sidebar, Header, Manajemen Diskon, Riwayat Penjualan, Tambah Produk Baru).

- **Frontend**: HTML + CSS + JavaScript murni (tanpa framework), per halaman.
- **Backend**: Python (Flask) + SQLite, menyediakan REST API (JSON).
- **Arsitektur**: Backend hanya mengirim data (API JSON). Halaman HTML dirender
  oleh Flask (Jinja2) sebagai "kerangka", lalu JavaScript di setiap halaman
  mengambil data dari API dan menampilkannya secara dinamis.

---

## 1. Struktur Folder

```
antari-admin/
├── backend/                     -> Server Python (Flask)
│   ├── app.py                   -> Entry point, mendaftarkan semua route
│   ├── database.py              -> Koneksi & helper SQLite
│   ├── schema.sql                -> Struktur tabel database
│   ├── seed.py                   -> Pengisi data contoh (produk, diskon, transaksi)
│   ├── utils.py                  -> Fungsi hitung statistik penjualan
│   ├── requirements.txt
│   └── routes/
│       ├── pages.py              -> Route halaman (render HTML)
│       ├── api_produk.py         -> CRUD API Produk
│       ├── api_diskon.py         -> CRUD API Diskon + statistik
│       └── api_penjualan.py      -> API riwayat penjualan + export Excel
│
└── frontend/                    -> Tampilan (HTML/CSS/JS)
    ├── templates/
    │   ├── base.html              -> Layout dasar (sidebar + header + content)
    │   ├── dashboard.html
    │   ├── manage_produk.html
    │   ├── tambah_produk.html
    │   ├── diskon.html
    │   ├── riwayat_penjualan.html
    │   ├── placeholder.html       -> Untuk Settings/Support/Logout
    │   └── partials/sidebar.html
    └── static/
        ├── css/style.css          -> Semua styling (1 file, terorganisir per bagian)
        ├── js/
        │   ├── api.js              -> Helper fetch & format Rupiah (dipakai semua halaman)
        │   ├── sidebar.js           -> Toggle sidebar di mobile
        │   ├── dashboard.js
        │   ├── produk.js
        │   ├── tambah_produk.js
        │   ├── diskon.js
        │   └── penjualan.js
        └── uploads/                -> Tempat foto produk yang diunggah disimpan
```

**Kenapa dipisah begini?** Supaya tiap halaman punya file JS & template-nya
sendiri (mudah dicari & di-maintain), sementara backend murni jadi "penyedia
data" lewat endpoint `/api/...`. Kalau nanti frontend mau diganti jadi React
atau Vue, backend tidak perlu diubah sama sekali.

---

## 2. Pemetaan Halaman Figma → Kode

| Frame di Figma | Halaman | URL | Template | API yang dipakai |
|---|---|---|---|---|
| Aside (3 state) | Sidebar di semua halaman | - | `partials/sidebar.html` | - |
| Header - Top App Bar | Header halaman Diskon | `/diskon` | `diskon.html` | - |
| Header - TopAppBar | Header halaman Riwayat Penjualan | `/penjualan` | `riwayat_penjualan.html` | - |
| Main Content (Diskon) | Tabel & statistik diskon | `/diskon` | `diskon.html` | `/api/diskon`, `/api/diskon/stats` |
| Main Content-1 (Penjualan) | Statistik, grafik, tabel transaksi | `/penjualan` | `riwayat_penjualan.html` | `/api/penjualan` |
| Main Shell (Tambah Produk Baru) | Form tambah produk | `/produk/tambah` | `tambah_produk.html` | `POST /api/produk` |

Dashboard (`/`) dan daftar Manage Produk (`/produk`) belum ada di frame yang
dibagikan, sehingga saya membuatkan versi yang konsisten dengan gaya desain
yang sama (warna, kartu, tabel). Silakan revisi kapan saja kalau Anda punya
desain pasti untuk dua halaman itu.

---

## 3. Cara Menjalankan (Step by Step)

### Langkah 1 — Pastikan Python terpasang
Buka terminal, cek versi Python (minimal 3.10):
```bash
python3 --version
```

### Langkah 2 — Masuk ke folder backend
```bash
cd antari-admin/backend
```

### Langkah 3 — (Disarankan) buat virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### Langkah 4 — Install dependency
```bash
pip install -r requirements.txt
```
Ini akan menginstall **Flask** (web server) dan **openpyxl** (untuk fitur
Export Excel).

### Langkah 5 — Jalankan server
```bash
python app.py
```
Saat pertama kali dijalankan, aplikasi otomatis:
1. Membuat file database `antari.db` di folder `backend/`.
2. Mengisi data contoh (7 produk, 3 diskon, ±150 transaksi 30 hari terakhir)
   lewat `seed.py`, supaya tampilan langsung terlihat berisi seperti di Figma.

### Langkah 6 — Buka di browser
```
http://127.0.0.1:5000
```
Anda akan diarahkan ke halaman **Dashboard**. Coba buka juga:
- `http://127.0.0.1:5000/produk`
- `http://127.0.0.1:5000/produk/tambah`
- `http://127.0.0.1:5000/diskon`
- `http://127.0.0.1:5000/penjualan`

### Langkah 7 — Reset data (opsional)
Kalau ingin mengulang dari data contoh yang fresh:
```bash
rm antari.db          # hapus database lama
python app.py          # jalankan lagi, akan otomatis dibuat & diisi ulang
```
atau jalankan seed secara manual:
```bash
python seed.py
```

---

## 4. Daftar Endpoint API

| Method | Endpoint | Keterangan |
|---|---|---|
| GET | `/api/produk?search=` | Daftar produk |
| POST | `/api/produk` | Tambah produk (multipart, bisa sertakan foto) |
| PUT | `/api/produk/<id>` | Update produk |
| DELETE | `/api/produk/<id>` | Hapus produk |
| GET | `/api/diskon` | Daftar diskon |
| POST | `/api/diskon` | Tambah diskon (JSON) |
| PUT | `/api/diskon/<id>` | Update diskon |
| DELETE | `/api/diskon/<id>` | Hapus diskon |
| GET | `/api/diskon/stats` | Statistik kartu "Total Diskon Digunakan" & "Potongan Harga Berjalan" |
| GET | `/api/penjualan?range=&start=&end=&search=&page=&per_page=` | Statistik + grafik + produk terlaris + tabel transaksi |
| GET | `/api/penjualan/export?...` | Unduh data transaksi sebagai file `.xlsx` |

`range` bisa berisi `harian`, `mingguan`, atau `bulanan`. Jika `start` & `end`
dikirim (format `YYYY-MM-DD`), itu yang dipakai (mengikuti date-picker di UI).

---

## 5. Mengganti Database (opsional, untuk production)

Saat ini pakai **SQLite** (`backend/antari.db`) — cocok untuk
development/demo karena tanpa instalasi tambahan. Untuk production dengan
banyak pengguna sekaligus, disarankan pindah ke **PostgreSQL/MySQL**:

1. Install driver-nya, contoh PostgreSQL: `pip install psycopg2-binary`
2. Ganti isi `database.py` agar `get_connection()` memakai
   `psycopg2.connect(...)` dengan kredensial server Anda.
3. Sesuaikan placeholder query dari `?` (gaya SQLite) ke `%s` (gaya psycopg2)
   di file-file `routes/api_*.py` dan `utils.py`.

Karena seluruh akses database dipusatkan di `database.py` /`utils.py`, Anda
tidak perlu mengubah banyak file lain.

---

## 6. Yang Bisa Dikembangkan Selanjutnya

- Sistem login & autentikasi (saat ini tombol Logout hanya menuju halaman
  placeholder, belum ada sesi login sungguhan).
- Halaman edit produk & edit diskon (saat ini baru tambah + hapus; tombol
  pensil di desain bisa dihubungkan ke modal/form edit yang serupa dengan
  form tambah).
- Halaman Settings & Support sesuai kebutuhan Anda.
- Validasi & pesan error yang lebih detail per field form.
- Upload foto produk ke cloud storage (S3/Cloud Storage) untuk deployment
  production, karena saat ini foto disimpan di folder lokal `frontend/static/uploads/`.

---

Kalau ada bagian desain yang saya tafsirkan kurang tepat (warna, ukuran,
urutan kolom, dll), beri tahu saya — saya bisa langsung sesuaikan ke kode
yang sudah ada.
