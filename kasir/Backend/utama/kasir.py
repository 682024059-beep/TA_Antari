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
    tanggal_mulai = request.args.get('tanggal_mulai', '').strip()
    tanggal_selesai = request.args.get('tanggal_selesai', '').strip()

    transaksi_filter = RIWAYAT_TRANSAKSI

    if tanggal_mulai:
        transaksi_filter = [
            item for item in transaksi_filter
            if item.get('tanggal_iso', '') >= tanggal_mulai
        ]

    if tanggal_selesai:
        transaksi_filter = [
            item for item in transaksi_filter
            if item.get('tanggal_iso', '') <= tanggal_selesai
        ]

    total_transaksi = len(transaksi_filter)
    total_pendapatan = sum(item.get('total', 0) for item in transaksi_filter)
    rata_rata = total_pendapatan // total_transaksi if total_transaksi > 0 else 0

    return render_template(
        'riwayat.html',
        transaksi=transaksi_filter,
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
        rata_rata=rata_rata,
        username=session.get('username', 'Kasir')
    )


@utama_kasir.route('/api/transaksi', methods=['POST'])
@login_required
def proses_transaksi():
    data = request.get_json(silent=True) or {}

    now = datetime.now()

    tanggal_frontend = data.get('tanggal', '').strip()
    waktu_frontend = data.get('waktu', '').strip()

    customer = data.get('customer', '').strip()
    items = data.get('items', [])
    metode = data.get('metode', 'Cash')
    total = int(data.get('total', 0) or 0)
    subtotal = int(data.get('subtotal', 0) or total)
    diskon = int(data.get('diskon', 0) or 0)
    bayar = int(data.get('bayar', 0) or 0)
    kembalian = int(data.get('kembalian', 0) or 0)

    if not items:
        return jsonify({
            'status': 'error',
            'message': 'Keranjang masih kosong. Pilih produk terlebih dahulu.'
        }), 400

    if not customer:
        return jsonify({
            'status': 'error',
            'message': 'Nama customer wajib diisi.'
        }), 400

    if total <= 0:
        return jsonify({
            'status': 'error',
            'message': 'Total transaksi tidak valid.'
        }), 400

    if bayar <= 0:
        return jsonify({
            'status': 'error',
            'message': 'Jumlah dibayar wajib diisi.'
        }), 400

    if bayar < total:
        return jsonify({
            'status': 'error',
            'message': 'Jumlah dibayar masih kurang.'
        }), 400

    if not metode:
        metode = 'Cash'

    tanggal_tampil = tanggal_frontend if tanggal_frontend else now.strftime('%d/%m/%Y')
    waktu_tampil = waktu_frontend if waktu_frontend else now.strftime('%H:%M:%S')
    tanggal_iso = now.strftime('%Y-%m-%d')

    transaksi_baru = {
        'no': f"TRX-{now.strftime('%H%M%S')}",
        'tanggal': tanggal_tampil,
        'tanggal_iso': tanggal_iso,
        'customer': customer,
        'produk': ', '.join([item.get('nama', '') for item in items]),
        'items': items,
        'subtotal': subtotal,
        'diskon': diskon,
        'total': total,
        'bayar': bayar,
        'kembalian': kembalian,
        'metode': metode,
        'waktu': waktu_tampil
    }

    # Sementara belum disimpan ke database.
    # Nanti bagian ini akan diganti INSERT ke tabel transaksi.
    RIWAYAT_TRANSAKSI.append(transaksi_baru)

    return jsonify({
        'status': 'success',
        'message': 'Pembayaran berhasil diproses!',
        'no': transaksi_baru['no'],
        'data': transaksi_baru
    })