from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import pymysql
from pymysql.cursors import DictCursor

load_dotenv(find_dotenv())

utama_kasir = Blueprint('utama_kasir', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('utama_auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================================
# KONEKSI DATABASE TIDB
# ==========================================================
def get_db_connection():
    db_host = os.getenv("DB_HOST")
    db_port = int(os.getenv("DB_PORT", 4000))
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_ssl = os.getenv("DB_SSL", "true").lower() in ("true", "1", "yes", "required")

    if not all([db_host, db_user, db_password, db_name]):
        raise RuntimeError("Konfigurasi database belum lengkap. Cek file .env kasir.")

    config = {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_password,
        "database": db_name,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
    }

    if db_ssl:
        config["ssl"] = {}

    return pymysql.connect(**config)


def format_rupiah(value):
    return f"Rp {int(value or 0):,}".replace(",", ".")


def parse_int(value, default=0):
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def buat_id_transaksi():
    now = datetime.now()
    return f"TRX{now.strftime('%y%m%d%H%M%S')}{now.microsecond // 1000:03d}"


def metode_ke_database(metode):
    metode = (metode or "").strip().lower()

    if metode in ("cash", "tunai"):
        return "Tunai"

    if metode == "qris":
        return "QRIS"

    return ""


def metode_ke_tampilan(metode):
    if metode == "Tunai":
        return "Cash"

    if metode == "QRIS":
        return "QRIS"

    return metode or "-"


# ==========================================================
# AMBIL PRODUK DARI DATABASE ADMIN
# ==========================================================
def ambil_produk_aktif():
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    kode,
                    nama,
                    kategori,
                    harga,
                    stok,
                    status,
                    foto_url
                FROM produk
                WHERE status = 'Aktif'
                  AND stok > 0
                ORDER BY kategori ASC, nama ASC
            """)

            return cursor.fetchall()

    finally:
        conn.close()


def ambil_kategori_produk(produk):
    return sorted(list(set([
        item.get("kategori")
        for item in produk
        if item.get("kategori")
    ])))


# ==========================================================
# HALAMAN KASIR
# ==========================================================
@utama_kasir.route('/kasir')
@login_required
def halaman_kasir():
    try:
        produk = ambil_produk_aktif()
        kategori_produk = ambil_kategori_produk(produk)
        db_error = None

    except Exception as e:
        produk = []
        kategori_produk = []
        db_error = str(e)

    return render_template(
        'kasir.html',
        produk=produk,
        kategori_produk=kategori_produk,
        metode_pembayaran=[],
        username=session.get('username', 'Kasir'),
        db_error=db_error
    )


# ==========================================================
# HALAMAN RIWAYAT TRANSAKSI
# ==========================================================
@utama_kasir.route('/riwayat')
@login_required
def halaman_riwayat():
    tanggal_mulai = request.args.get('tanggal_mulai', '').strip()
    tanggal_selesai = request.args.get('tanggal_selesai', '').strip()

    conn = None

    try:
        conn = get_db_connection()

        where_clause = []
        params = []

        if tanggal_mulai:
            where_clause.append("t.tanggal >= %s")
            params.append(tanggal_mulai)

        if tanggal_selesai:
            where_clause.append("t.tanggal <= %s")
            params.append(tanggal_selesai)

        where_sql = ""
        if where_clause:
            where_sql = "WHERE " + " AND ".join(where_clause)

        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    t.id AS no,
                    DATE_FORMAT(t.tanggal, '%%d/%%m/%%Y') AS tanggal,
                    DATE_FORMAT(t.tanggal, '%%Y-%%m-%%d') AS tanggal_iso,
                    t.waktu,
                    t.nama_customer AS customer,
                    t.subtotal,
                    t.diskon_nominal AS diskon,
                    t.total,
                    t.bayar,
                    t.kembalian,
                    t.metode,
                    COALESCE(
                        GROUP_CONCAT(
                            CONCAT(ti.nama, ' x', ti.qty)
                            SEPARATOR ', '
                        ),
                        '-'
                    ) AS produk
                FROM transaksi t
                LEFT JOIN transaksi_items ti
                    ON ti.transaksi_id = t.id
                {where_sql}
                GROUP BY
                    t.id,
                    t.tanggal,
                    t.waktu,
                    t.nama_customer,
                    t.subtotal,
                    t.diskon_nominal,
                    t.total,
                    t.bayar,
                    t.kembalian,
                    t.metode,
                    t.created_at
                ORDER BY t.created_at DESC
            """, params)

            transaksi = cursor.fetchall()

        for item in transaksi:
            item["metode"] = metode_ke_tampilan(item.get("metode"))
            item["customer"] = item.get("customer") or "-"
            item["produk"] = item.get("produk") or "-"

        total_transaksi = len(transaksi)
        total_pendapatan = sum(parse_int(item.get('total')) for item in transaksi)
        rata_rata = total_pendapatan // total_transaksi if total_transaksi > 0 else 0

    except Exception as e:
        transaksi = []
        total_transaksi = 0
        total_pendapatan = 0
        rata_rata = 0
        print("ERROR RIWAYAT:", e)

    finally:
        if conn:
            conn.close()

    return render_template(
        'riwayat.html',
        transaksi=transaksi,
        total_transaksi=total_transaksi,
        total_pendapatan=total_pendapatan,
        rata_rata=rata_rata,
        username=session.get('username', 'Kasir')
    )


# ==========================================================
# PROSES TRANSAKSI KASIR
# ==========================================================
@utama_kasir.route('/api/transaksi', methods=['POST'])
@login_required
def proses_transaksi():
    data = request.get_json(silent=True) or {}

    now = datetime.now()
    conn = None

    customer = (data.get('customer') or '').strip()
    items = data.get('items', [])
    metode_frontend = data.get('metode', '')
    metode_db = metode_ke_database(metode_frontend)

    bayar_frontend = parse_int(data.get('bayar'))
    kembalian_frontend = parse_int(data.get('kembalian'))

    if not customer:
        return jsonify({
            'status': 'error',
            'message': 'Nama customer wajib diisi.'
        }), 400

    if not items:
        return jsonify({
            'status': 'error',
            'message': 'Keranjang masih kosong. Pilih produk terlebih dahulu.'
        }), 400

    if not metode_db:
        return jsonify({
            'status': 'error',
            'message': 'Pilih metode pembayaran Cash atau QRIS.'
        }), 400

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            transaksi_items = []
            subtotal_hitung = 0

            # Ambil ulang produk dari database supaya harga dan stok valid
            for item in items:
                kode_produk = (
                    item.get('kode')
                    or item.get('kode_produk')
                    or item.get('id')
                    or ''
                ).strip()

                qty = parse_int(item.get('qty'), 1)

                if not kode_produk:
                    raise ValueError("Kode produk tidak valid.")

                if qty <= 0:
                    raise ValueError("Jumlah produk tidak valid.")

                cursor.execute("""
                    SELECT
                        kode,
                        nama,
                        harga,
                        stok,
                        status
                    FROM produk
                    WHERE kode = %s
                      AND status = 'Aktif'
                    FOR UPDATE
                """, (kode_produk,))

                produk_db = cursor.fetchone()

                if not produk_db:
                    raise ValueError(f"Produk {kode_produk} tidak ditemukan atau tidak aktif.")

                if parse_int(produk_db.get('stok')) < qty:
                    raise ValueError(f"Stok {produk_db.get('nama')} tidak mencukupi.")

                harga = parse_int(produk_db.get('harga'))
                subtotal_item = harga * qty
                subtotal_hitung += subtotal_item

                transaksi_items.append({
                    'kode_produk': produk_db.get('kode'),
                    'nama': produk_db.get('nama'),
                    'harga': harga,
                    'qty': qty,
                    'subtotal': subtotal_item
                })

            # Diskon sementara belum digunakan
            diskon_nominal = 0
            diskon_id = None
            total_hitung = subtotal_hitung - diskon_nominal

            if total_hitung <= 0:
                raise ValueError("Total transaksi tidak valid.")

            if metode_db == "QRIS":
                bayar = total_hitung
                kembalian = 0
            else:
                bayar = bayar_frontend
                kembalian = bayar - total_hitung

                if bayar <= 0:
                    raise ValueError("Jumlah dibayar wajib diisi.")

                if bayar < total_hitung:
                    raise ValueError("Jumlah dibayar masih kurang.")

            transaksi_id = buat_id_transaksi()
            tanggal_db = now.strftime('%Y-%m-%d')
            tanggal_tampil = now.strftime('%d/%m/%Y')
            waktu_tampil = now.strftime('%H:%M:%S')
            kasir_username = session.get('username', 'Kasir')

            cursor.execute("""
                INSERT INTO transaksi (
                    id,
                    tanggal,
                    waktu,
                    subtotal,
                    diskon_nominal,
                    diskon_id,
                    total,
                    bayar,
                    kembalian,
                    metode,
                    kasir_username,
                    nama_customer,
                    email_customer,
                    struk_terkirim
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                transaksi_id,
                tanggal_db,
                waktu_tampil,
                subtotal_hitung,
                diskon_nominal,
                diskon_id,
                total_hitung,
                bayar,
                kembalian,
                metode_db,
                kasir_username,
                customer,
                None,
                0
            ))

            for item in transaksi_items:
                cursor.execute("""
                    INSERT INTO transaksi_items (
                        transaksi_id,
                        kode_produk,
                        nama,
                        harga,
                        qty,
                        subtotal
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                """, (
                    transaksi_id,
                    item['kode_produk'],
                    item['nama'],
                    item['harga'],
                    item['qty'],
                    item['subtotal']
                ))

                cursor.execute("""
                    UPDATE produk
                    SET stok = stok - %s
                    WHERE kode = %s
                      AND stok >= %s
                """, (
                    item['qty'],
                    item['kode_produk'],
                    item['qty']
                ))

                if cursor.rowcount == 0:
                    raise ValueError(f"Gagal mengurangi stok produk {item['nama']}.")

            cursor.execute("""
                INSERT INTO notifikasi (
                    target_role,
                    tipe,
                    judul,
                    pesan,
                    ref_kode
                ) VALUES (
                    'admin',
                    'transaksi_baru',
                    'Transaksi Baru',
                    %s,
                    %s
                )
            """, (
                f"Transaksi {transaksi_id} dari kasir {kasir_username} berhasil diproses.",
                transaksi_id
            ))

        conn.commit()

        produk_ringkas = ', '.join([
            item['nama'] for item in transaksi_items
        ])

        transaksi_baru = {
            'no': transaksi_id,
            'tanggal': tanggal_tampil,
            'tanggal_iso': tanggal_db,
            'customer': customer,
            'produk': produk_ringkas,
            'items': transaksi_items,
            'subtotal': subtotal_hitung,
            'diskon': diskon_nominal,
            'total': total_hitung,
            'bayar': bayar,
            'kembalian': kembalian,
            'metode': metode_ke_tampilan(metode_db),
            'waktu': waktu_tampil
        }

        return jsonify({
            'status': 'success',
            'message': 'Pembayaran berhasil diproses!',
            'no': transaksi_id,
            'data': transaksi_baru
        })

    except ValueError as e:
        if conn:
            conn.rollback()

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

    except Exception as e:
        if conn:
            conn.rollback()

        print("ERROR TRANSAKSI:", e)

        return jsonify({
            'status': 'error',
            'message': 'Terjadi kesalahan saat menyimpan transaksi ke database.'
        }), 500

    finally:
        if conn:
            conn.close()
            
@utama_kasir.route('/api/notifikasi/kasir', methods=['GET'])
@login_required
def ambil_notifikasi_kasir():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    judul,
                    pesan,
                    tipe,
                    ref_kode,
                    is_read,
                    DATE_FORMAT(created_at, '%%d/%%m/%%Y %%H:%%i') AS created_at
                FROM notifikasi
                WHERE target_role IN ('kasir', 'all')
                ORDER BY created_at DESC
                LIMIT 10
            """)

            notifikasi = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM notifikasi
                WHERE target_role IN ('kasir', 'all')
                  AND is_read = 0
            """)

            unread = cursor.fetchone()

        return jsonify({
            'status': 'success',
            'data': notifikasi,
            'unread_count': unread.get('total', 0) if unread else 0
        })

    except Exception as e:
        print("ERROR NOTIFIKASI KASIR:", e)

        return jsonify({
            'status': 'error',
            'message': 'Gagal mengambil notifikasi.'
        }), 500

    finally:
        if conn:
            conn.close()


@utama_kasir.route('/api/notifikasi/kasir/read', methods=['POST'])
@login_required
def baca_notifikasi_kasir():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE notifikasi
                SET is_read = 1
                WHERE target_role IN ('kasir', 'all')
                  AND is_read = 0
            """)

        conn.commit()

        return jsonify({
            'status': 'success',
            'message': 'Notifikasi sudah dibaca.'
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("ERROR BACA NOTIFIKASI:", e)

        return jsonify({
            'status': 'error',
            'message': 'Gagal memperbarui notifikasi.'
        }), 500

    finally:
        if conn:
            conn.close()