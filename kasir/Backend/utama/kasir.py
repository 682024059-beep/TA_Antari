from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime

utama_kasir = Blueprint('utama_kasir', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('utama_auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================
# DATA SEMENTARA
# ==========================================================
# Untuk saat ini dikosongkan dulu.
# Nanti data ini akan diganti dari database/admin.
DATA_PRODUK = []

METODE_PEMBAYARAN = []

RIWAYAT_TRANSAKSI = []


@utama_kasir.route('/kasir')
@login_required
def halaman_kasir():
    kategori_produk = sorted(list(set([p.get('kategori') for p in DATA_PRODUK if p.get('kategori')])))

    return render_template(
        'kasir.html',
        produk=DATA_PRODUK,
        kategori_produk=kategori_produk,
        metode_pembayaran=METODE_PEMBAYARAN,
        username=session.get('username', 'Kasir')
    )


@utama_kasir.route('/riwayat')
@login_required
def halaman_riwayat():
    total_transaksi = len(RIWAYAT_TRANSAKSI)
    total_pendapatan = sum(item.get('total', 0) for item in RIWAYAT_TRANSAKSI)
    rata_rata = total_pendapatan // total_transaksi if total_transaksi > 0 else 0

    return render_template(
        'riwayat.html',
        transaksi=RIWAYAT_TRANSAKSI,
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
        rata_rata=rata_rata,
        username=session.get('username', 'Kasir')
    )


@utama_kasir.route('/api/transaksi', methods=['POST'])
@login_required
def proses_transaksi():
    data = request.get_json(silent=True) or {}

    customer = data.get('customer', '').strip()
    meja = data.get('meja', '').strip()
    items = data.get('items', [])
    metode = data.get('metode', '')
    total = data.get('total', 0)

    if not items:
        return jsonify({
            'status': 'error',
            'message': 'Keranjang masih kosong. Pilih produk terlebih dahulu.'
        }), 400

    if not metode:
        return jsonify({
            'status': 'error',
            'message': 'Metode pembayaran belum dipilih.'
        }), 400

    transaksi_baru = {
        'no': f"TRX-{datetime.now().strftime('%H%M%S')}",
        'customer': customer if customer else 'Customer Umum',
        'meja': meja if meja else '-',
        'produk': ', '.join([item.get('nama', '') for item in items]),
        'total': total,
        'metode': metode,
        'waktu': datetime.now().strftime('%H:%M')
    }

    # Sementara belum disimpan ke database.
    # Nanti bagian ini akan diganti INSERT ke tabel transaksi.
    RIWAYAT_TRANSAKSI.append(transaksi_baru)

    return jsonify({
        'status': 'success',
        'message': 'Pembayaran berhasil diproses!',
        'data': transaksi_baru
    })