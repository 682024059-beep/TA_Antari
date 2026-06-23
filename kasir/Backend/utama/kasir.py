from flask import Blueprint, render_template, request, jsonify

utama_kasir = Blueprint('utama_kasir', __name__)

# DATA DUMMY MENU KASIR (Sesuai Gambar Mockup Screenshot 2026-06-23 134408.png)
DATA_PRODUK = [
    {"id": "KP-001", "nama": "Antari Signature Latte", "harga": 32000, "kategori": "Coffee", "status": "tersedia"},
    {"id": "KP-002", "nama": "Iced Americano", "harga": 28000, "kategori": "Coffee", "status": "tersedia"},
    {"id": "KP-015", "nama": "Butter Croissant", "harga": 24000, "kategori": "Makanan Ringan", "status": "stok habis"},
    {"id": "KP-005", "nama": "Kyoto Matcha Latte", "harga": 35000, "kategori": "Non-Coffee", "status": "tersedia"}
]

@utama_kasir.route('/kasir')
def halaman_kasir():
    # Kirim data dummy ke file HTML kasir
    return render_template('kasir.html', produk=DATA_PRODUK)

@utama_kasir.route('/riwayat')
def halaman_riwayat():
    # Data dummy untuk log transaksi terbaru (Sesuai Screenshot 2026-06-23 134355.png)
    riwayat_dummy = [
        {"no": "TRX-04220", "customer": "Aditya Pratama", "meja": "04", "produk": "Caramel Macchiato, Espresso", "total": 124000, "metode": "CASH", "waktu": "14:20"},
        {"no": "TRX-04219", "customer": "Siska Wijaya", "meja": "12", "produk": "Hot Americano, Croissant", "total": 68000, "metode": "CASHLESS", "waktu": "14:05"},
        {"no": "TRX-04218", "customer": "Rian Hidayat", "meja": "08", "produk": "V60 Ethiopia, Brownies", "total": 85500, "metode": "CASHLESS", "waktu": "13:48"},
        {"no": "TRX-04217", "customer": "Dina Maria", "meja": "TA", "produk": "Iced Latte x2", "total": 76000, "metode": "CASH", "waktu": "13:30"}
    ]
    return render_template('riwayat.html', transaksi=riwayat_dummy)

@utama_kasir.route('/api/transaksi', methods=['POST'])
def proses_transaksi():
    return jsonify({"status": "success", "message": "Pembayaran Berhasil Diproses!"})