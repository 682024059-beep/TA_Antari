from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os
import pymysql
import certifi
import base64
import requests
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

    if not all([db_host, db_user, db_password, db_name]):
        raise RuntimeError("Konfigurasi database belum lengkap. Cek file .env kasir.")

    config = {
        "host": db_host,
        "port": db_port,
        "user": db_user,
        "password": db_password,
        "database": db_name,
        "cursorclass": DictCursor,
        "charset": "utf8mb4",
        "autocommit": False,
        "ssl": {
            "ca": certifi.where()
        }
    }

    return pymysql.connect(**config)


def format_rupiah(value):
    return f"Rp {int(value or 0):,}".replace(",", ".")


def parse_int(value, default=0):
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default

BATAS_STOK_MENIPIS = 8


def buat_notifikasi_stok_admin(cursor, produk, stok_lama, stok_baru):
    """
    Membuat notifikasi admin saat stok produk menipis/habis karena transaksi kasir.
    Dibuat setiap ada pembelian yang membuat stok berada di batas menipis/habis.
    """

    kode = produk.get("kode")
    nama = produk.get("nama")

    if not kode or not nama:
        return None

    try:
        stok_lama = int(stok_lama or 0)
        stok_baru = int(stok_baru or 0)
    except Exception:
        return None

    if stok_baru < 0:
        stok_baru = 0

    # Kalau stok tidak berkurang, tidak perlu notif
    if stok_baru >= stok_lama:
        return None

    if stok_baru <= 0:
        tipe = "stok_habis"
        judul = "Stok Habis"
        pesan = f'Stok "{nama}" ({kode}) telah habis karena transaksi kasir.'
    elif stok_baru <= BATAS_STOK_MENIPIS:
        tipe = "stok_menipis"
        judul = "Stok Menipis"
        pesan = f'Stok "{nama}" ({kode}) tersisa {stok_baru} unit setelah transaksi kasir.'
    else:
        return None

    cursor.execute("""
        INSERT INTO notifikasi (
            target_role,
            tipe,
            judul,
            pesan,
            ref_kode
        ) VALUES (
            'admin',
            %s,
            %s,
            %s,
            %s
        )
    """, (
        tipe,
        judul,
        pesan,
        kode
    ))

    return {
        "kode": kode,
        "nama": nama,
        "stok": stok_baru,
        "tipe": tipe
    }

def ambil_email_admin_notifikasi():
    """
    Mengambil email admin aktif dari database.
    Jadi kalau admin mengganti email di Profil Saya,
    notifikasi email akan dikirim ke email terbaru.
    """

    emails = []
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT email
                FROM users
                WHERE LOWER(role) = 'admin'
                  AND email IS NOT NULL
                  AND TRIM(email) <> ''
                  AND is_active = 1
            """)

            rows = cursor.fetchall()

        for row in rows:
            email = (row.get("email") or "").strip().lower()

            if email and email not in emails:
                emails.append(email)

    except Exception as err:
        print("[Email Admin] Gagal mengambil email admin dari database:", err)

    finally:
        if conn:
            conn.close()

    if not emails:
        env_email = os.getenv("RESEND_ADMIN_EMAIL", "").strip().lower()

        if env_email:
            emails.append(env_email)

    return emails

def kirim_email_stok_admin_dari_kasir(produk_list):
    """
    Kirim email stok menipis/habis dari aplikasi kasir.
    Pakai Resend REST API supaya kasir tidak perlu import file Admin.
    """

    if not produk_list:
        return

    api_key = os.getenv("RESEND_API_KEY", "").strip()
    admin_emails = ambil_email_admin_notifikasi()
    from_email = os.getenv(
        "RESEND_FROM_EMAIL",
        "ANTARI CoffeeShop <onboarding@resend.dev>"
    ).strip()

    if not api_key or not admin_emails:
        print("[Resend Kasir] RESEND_API_KEY belum diset atau email admin tidak ditemukan.")
    return

    rows = ""

    for p in produk_list:
        rows += f"""
        <tr>
            <td style="padding:8px 10px; border-bottom:1px solid #eee;">{p.get("kode")}</td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee;">{p.get("nama")}</td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee; text-align:center;">
                {p.get("stok")}
            </td>
            <td style="padding:8px 10px; border-bottom:1px solid #eee;">
                {"Habis" if p.get("tipe") == "stok_habis" else "Menipis"}
            </td>
        </tr>
        """

    html = f"""
    <div style="font-family:Arial,sans-serif; max-width:560px; margin:auto; color:#2b2118;">
        <h2>⚠️ Peringatan Stok Produk ANTARI</h2>

        <p>
            Ada produk yang stoknya menipis atau habis setelah transaksi dari kasir.
            Silakan lakukan pengecekan dan restock produk.
        </p>

        <table style="width:100%; border-collapse:collapse; font-size:14px; border:1px solid #eee;">
            <thead>
                <tr style="background:#f6f1ea;">
                    <th style="padding:8px 10px; text-align:left;">Kode</th>
                    <th style="padding:8px 10px; text-align:left;">Nama Produk</th>
                    <th style="padding:8px 10px;">Sisa Stok</th>
                    <th style="padding:8px 10px; text-align:left;">Status</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <p style="margin-top:18px; font-size:12px; color:#9c8c7d;">
            Email otomatis dari Sistem POS ANTARI.
        </p>
    </div>
    """

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": from_email,
                "to": admin_emails,
                "subject": "Peringatan: Stok Produk Menipis/Habis",
                "html": html
            },
            timeout=15
        )

        if response.status_code not in [200, 201, 202]:
            print("[Resend Kasir] Gagal kirim email stok:", response.text)
        else:
            print("[Resend Kasir] Email stok berhasil dikirim.")

    except Exception as err:
        print("[Resend Kasir] Error kirim email stok:", err)

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


def hitung_diskon_backend(subtotal, diskon):
    if not diskon:
        return 0

    jenis = diskon.get("jenis")
    nilai = parse_int(diskon.get("nilai"))

    if nilai <= 0:
        return 0

    if jenis == "Persen":
        return round(subtotal * (nilai / 100))

    if jenis == "Nominal":
        return min(nilai, subtotal)

    return 0


@utama_kasir.route('/api/midtrans/token', methods=['POST'])
@login_required
def api_midtrans_token():
    data = request.get_json(silent=True) or {}

    customer = (data.get("customer") or "").strip()
    items = data.get("items", [])

    diskon_id_frontend = (
        data.get("diskon_id")
        or data.get("discount_id")
        or data.get("diskonId")
        or ""
    )
    diskon_id_frontend = str(diskon_id_frontend).strip()

    if not customer:
        return jsonify({
            "status": "error",
            "message": "Nama customer wajib diisi."
        }), 400

    if not items:
        return jsonify({
            "status": "error",
            "message": "Keranjang masih kosong."
        }), 400

    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            transaksi_items, subtotal, diskon_nominal, diskon_id, diskon_nama, total = hitung_order_midtrans(
                cursor,
                items,
                diskon_id_frontend
            )

        order_id = "MID-" + buat_id_transaksi()

        item_details = []

        for item in transaksi_items:
            item_details.append({
                "id": str(item["kode_produk"])[:50],
                "price": int(item["harga"]),
                "quantity": int(item["qty"]),
                "name": str(item["nama"])[:50],
            })

        if diskon_nominal > 0:
            item_details.append({
                "id": "DISKON",
                "price": -int(diskon_nominal),
                "quantity": 1,
                "name": str(diskon_nama or "Diskon")[:50],
            })

        payload = {
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": int(total),
            },
            "item_details": item_details,
            "customer_details": {
                "first_name": customer,
            },
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": midtrans_auth_header(),
        }

        response = requests.post(
            midtrans_snap_url(),
            json=payload,
            headers=headers,
            timeout=20,
        )

        result = response.json()

        if response.status_code not in (200, 201):
            print("[MIDTRANS ERROR]", result)

            return jsonify({
                "status": "error",
                "message": result.get("error_messages", ["Gagal membuat token Midtrans."])[0]
                if isinstance(result.get("error_messages"), list)
                else "Gagal membuat token Midtrans.",
                "detail": result,
            }), 400

        return jsonify({
            "status": "success",
            "token": result.get("token"),
            "redirect_url": result.get("redirect_url"),
            "order_id": order_id,
            "total": total,
            "subtotal": subtotal,
            "diskon": diskon_nominal,
            "diskon_id": diskon_id,
            "diskon_nama": diskon_nama,
        })

    except ValueError as err:
        return jsonify({
            "status": "error",
            "message": str(err),
        }), 400

    except Exception as err:
        print("[MIDTRANS TOKEN ERROR]", err)

        return jsonify({
            "status": "error",
            "message": "Terjadi kesalahan saat membuat pembayaran Midtrans.",
        }), 500

    finally:
        if conn:
            conn.close()

def midtrans_is_production():
    return str(os.getenv("MIDTRANS_IS_PRODUCTION", "false")).lower() == "true"


def midtrans_snap_url():
    if midtrans_is_production():
        return "https://app.midtrans.com/snap/v1/transactions"

    return "https://app.sandbox.midtrans.com/snap/v1/transactions"


def midtrans_auth_header():
    server_key = os.getenv("MIDTRANS_SERVER_KEY", "").strip()

    if not server_key:
        raise RuntimeError("MIDTRANS_SERVER_KEY belum diisi di file .env kasir.")

    auth_string = base64.b64encode(f"{server_key}:".encode("utf-8")).decode("utf-8")

    return f"Basic {auth_string}"


def hitung_order_midtrans(cursor, items, diskon_id_frontend):
    transaksi_items = []
    subtotal_hitung = 0

    for item in items:
        kode_produk = str(
            item.get("kode")
            or item.get("kode_produk")
            or item.get("id")
            or ""
        ).strip()

        qty = parse_int(item.get("qty"), 1)

        if not kode_produk:
            raise ValueError("Kode produk tidak valid.")

        if qty <= 0:
            raise ValueError("Jumlah produk tidak valid.")

        cursor.execute("""
            SELECT kode, nama, harga, stok, status
            FROM produk
            WHERE kode = %s
              AND status = 'Aktif'
            LIMIT 1
        """, (kode_produk,))

        produk_db = cursor.fetchone()

        if not produk_db:
            raise ValueError(f"Produk {kode_produk} tidak ditemukan atau tidak aktif.")

        if parse_int(produk_db.get("stok")) < qty:
            raise ValueError(f"Stok {produk_db.get('nama')} tidak mencukupi.")

        harga = parse_int(produk_db.get("harga"))
        subtotal_item = harga * qty
        subtotal_hitung += subtotal_item

        transaksi_items.append({
            "kode_produk": produk_db.get("kode"),
            "nama": produk_db.get("nama"),
            "harga": harga,
            "qty": qty,
            "subtotal": subtotal_item,
        })

    diskon_nominal = 0
    diskon_id = None
    diskon_nama = None

    if diskon_id_frontend:
        cursor.execute("""
            SELECT id, nama, jenis, nilai
            FROM diskon
            WHERE id = %s
              AND status = 'Aktif'
              AND CURDATE() BETWEEN mulai AND selesai
            LIMIT 1
        """, (diskon_id_frontend,))

        diskon_db = cursor.fetchone()

        if not diskon_db:
            raise ValueError("Diskon tidak valid atau sudah tidak aktif.")

        diskon_id = diskon_db.get("id")
        diskon_nama = diskon_db.get("nama")
        diskon_nominal = hitung_diskon_backend(subtotal_hitung, diskon_db)

    total_hitung = subtotal_hitung - diskon_nominal

    if total_hitung <= 0:
        raise ValueError("Total transaksi tidak valid.")

    return transaksi_items, subtotal_hitung, diskon_nominal, diskon_id, diskon_nama, total_hitung

def ambil_produk_aktif():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, kode, nama, kategori, harga, stok, status, foto_url
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


@utama_kasir.route('/kasir')
@login_required
def halaman_kasir():
    try:
        produk = ambil_produk_aktif()
        kategori_produk = ambil_kategori_produk(produk)
        db_error = None

        active_discount = {
            "id": "",
            "nama": "",
            "jenis": "",
            "nilai": 0
        }

    except Exception as e:
        print("ERROR HALAMAN KASIR:", e)

        produk = []
        kategori_produk = []
        db_error = str(e)

        active_discount = {
            "id": "",
            "nama": "",
            "jenis": "",
            "nilai": 0
        }

    return render_template(
    'kasir.html',
    produk=produk,
    kategori_produk=kategori_produk,
    metode_pembayaran=[],
    username=session.get('username', 'Kasir'),
    active_discount=active_discount,
    db_error=db_error,
    midtrans_client_key=os.getenv("MIDTRANS_CLIENT_KEY", "")
)


@utama_kasir.route('/api/diskon/aktif', methods=['GET'])
@login_required
def api_diskon_aktif():
    conn = None

    try:
        conn = get_db_connection()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, nama, jenis, nilai
                FROM diskon
                WHERE status = 'Aktif'
                  AND CURDATE() BETWEEN mulai AND selesai
                ORDER BY created_at DESC
            """)
            diskon = cursor.fetchall()

        return jsonify({
            "status": "success",
            "data": diskon
        })

    except Exception as e:
        print("ERROR API DISKON AKTIF:", e)

        return jsonify({
            "status": "error",
            "message": "Gagal mengambil diskon aktif."
        }), 500

    finally:
        if conn:
            conn.close()


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
    diskon_id_frontend = (
        data.get('diskon_id')
        or data.get('discount_id')
        or data.get('diskonId')
        or ''
    )

    diskon_id_frontend = str(diskon_id_frontend).strip()

    produk_stok_alert = []

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
            stok_lama_map = {}

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

                stok_lama = parse_int(produk_db.get('stok'))

                if stok_lama < qty:
                    raise ValueError(f"Stok {produk_db.get('nama')} tidak mencukupi.")

                harga = parse_int(produk_db.get('harga'))
                subtotal_item = harga * qty
                subtotal_hitung += subtotal_item

                stok_lama_map[kode_produk] = stok_lama

                transaksi_items.append({
                    'kode_produk': produk_db.get('kode'),
                    'nama': produk_db.get('nama'),
                    'harga': harga,
                    'qty': qty,
                    'subtotal': subtotal_item
                })

            diskon_nominal = 0
            diskon_id = None
            diskon_nama = None

            if diskon_id_frontend:
                cursor.execute("""
                    SELECT id, nama, jenis, nilai
                    FROM diskon
                    WHERE id = %s
                      AND status = 'Aktif'
                      AND CURDATE() BETWEEN mulai AND selesai
                    LIMIT 1
                """, (diskon_id_frontend,))

                diskon_db = cursor.fetchone()

                if not diskon_db:
                    raise ValueError("Diskon tidak valid atau sudah tidak aktif.")

                diskon_id = diskon_db.get("id")
                diskon_nama = diskon_db.get("nama")
                diskon_nominal = hitung_diskon_backend(subtotal_hitung, diskon_db)

            total_hitung = subtotal_hitung - diskon_nominal

            if total_hitung <= 0:
                raise ValueError("Total transaksi tidak valid.")

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

                stok_lama = parse_int(stok_lama_map.get(item['kode_produk']))
                stok_baru = stok_lama - parse_int(item['qty'])

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

                # Ambil data produk setelah stok dikurangi
                cursor.execute("""
                    SELECT kode, nama, stok
                    FROM produk
                    WHERE kode = %s
                    LIMIT 1
                """, (item['kode_produk'],))

                produk_update = cursor.fetchone()

                if produk_update:
                    alert = buat_notifikasi_stok_admin(
                        cursor,
                        produk_update,
                        stok_lama,
                        stok_baru
                    )

                    if alert:
                        produk_stok_alert.append(alert)

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

        # Kirim email setelah transaksi benar-benar berhasil commit
        if produk_stok_alert:
            kirim_email_stok_admin_dari_kasir(produk_stok_alert)

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
            'diskon_id': diskon_id,
            'diskon_nama': diskon_nama,
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
            'message': 'Terjadi kesalahan saat memproses transaksi.'
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
                ORDER BY created_at DESC, id DESC
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