from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps

utama_kasir = Blueprint('utama_kasir', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('utama_auth.login'))
        return f(*args, **kwargs)
    return decorated_function


DATA_PRODUK = [
    {
        'id': 'KP-001',
        'nama': 'Antari Signature Latte',
        'harga': 32000,
        'kategori': 'Coffee',
        'status': 'tersedia'
    },
    {
        'id': 'KP-002',
        'nama': 'Iced Americano',
        'harga': 28000,
        'kategori': 'Coffee',
        'status': 'tersedia'
    },
    {
        'id': 'KP-015',
        'nama': 'Butter Croissant',
        'harga': 24000,
        'kategori': 'Makanan Ringan',
        'status': 'stok habis'
    },
    {
        'id': 'KP-005',
        'nama': 'Kyoto Matcha Latte',
        'harga': 35000,
        'kategori': 'Non-Coffee',
        'status': 'tersedia'
    }
]


RIWAYAT_DUMMY = [
    {
        'no': 'TRX-04220',
        'customer': 'Aditya Pratama',
        'meja': '04',
        'produk': 'Caramel Macchiato, Espresso',
        'total': 124000,
        'metode': 'CASH',
        'waktu': '14:20'
    },
    {
        'no': 'TRX-04219',
        'customer': 'Siska Wijaya',
        'meja': '12',
        'produk': 'Hot Americano, Croissant',
        'total': 68000,
        'metode': 'CASHLESS',
        'waktu': '14:05'
    },
    {
        'no': 'TRX-04218',
        'customer': 'Rian Hidayat',
        'meja': '08',
        'produk': 'V60 Ethiopia, Brownies',
        'total': 85500,
        'metode': 'CASHLESS',
        'waktu': '13:48'
    },
    {
        'no': 'TRX-04217',
        'customer': 'Dina Maria',
        'meja': 'TA',
        'produk': 'Iced Latte x2',
        'total': 76000,
        'metode': 'CASH',
        'waktu': '13:30'
    }
]


@utama_kasir.route('/kasir')
@login_required
def halaman_kasir():
    return render_template(
        'kasir.html',
        produk=DATA_PRODUK,
        username=session.get('username', 'Kasir')
    )


@utama_kasir.route('/riwayat')
@login_required
def halaman_riwayat():
    total_transaksi = len(RIWAYAT_DUMMY)
    total_pendapatan = sum(item['total'] for item in RIWAYAT_DUMMY)
    rata_rata = total_pendapatan // total_transaksi if total_transaksi > 0 else 0

    return render_template(
        'riwayat.html',
        transaksi=RIWAYAT_DUMMY,
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
        rata_rata=rata_rata,
        username=session.get('username', 'Kasir')
    )


@utama_kasir.route('/api/transaksi', methods=['POST'])
@login_required
def proses_transaksi():
    data = request.get_json()

    return jsonify({
        'status': 'success',
        'message': 'Pembayaran berhasil diproses!',
        'data': data
    })