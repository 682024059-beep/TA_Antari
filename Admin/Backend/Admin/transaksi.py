"""
Transaksi (kasir) — simpan transaksi + item, kurangi stok, kirim
struk digital via Resend jika email pelanggan diisi, trigger
notifikasi jika ada stok yang jadi menipis/habis.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from db_conn import get_db, query
from Backend.Utils.auth import auth_required
from Backend.Utils.notify import create_notifikasi
from Backend.Utils.resend_util import send_struk_email, send_stok_menipis_email

bp = Blueprint("transaksi", __name__, url_prefix="/api/transaksi")
THRESHOLD = 8


@bp.get("")
@auth_required
def list_transaksi():
    start = request.args.get("start")
    end = request.args.get("end")

    sql = "SELECT * FROM transaksi"
    params = []
    conds = []
    if start:
        conds.append("tanggal >= %s")
        params.append(start)
    if end:
        conds.append("tanggal <= %s")
        params.append(end)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY created_at DESC"

    trx_rows = query(sql, params)
    ids = [t["id"] for t in trx_rows]
    items_by_trx = {}
    if ids:
        placeholders = ",".join(["%s"] * len(ids))
        items = query(f"SELECT * FROM transaksi_items WHERE transaksi_id IN ({placeholders})", ids)
        for it in items:
            items_by_trx.setdefault(it["transaksi_id"], []).append(it)

    result = []
    for t in trx_rows:
        t = dict(t)
        t["items"] = items_by_trx.get(t["id"], [])
        result.append(t)
    return jsonify({"transaksi": result})


@bp.post("")
@auth_required
def create_transaksi():
    data = request.get_json(silent=True) or {}
    items = data.get("items") or []
    if not items:
        return jsonify({"message": "Keranjang transaksi kosong."}), 400

    subtotal = data.get("subtotal", 0)
    diskon_nominal = data.get("diskon_nominal", 0)
    diskon_id = data.get("diskon_id")
    total = data.get("total", 0)
    metode = data.get("metode") or "Tunai"
    nama_customer = data.get("nama_customer")
    email_customer = data.get("email_customer")

    conn = get_db()
    try:
        conn.autocommit(False)
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(id,5) AS UNSIGNED)),1000) as maxNum FROM transaksi")
            max_num = cur.fetchone()["maxNum"]
            trx_id = f"TRX-{max_num + 1}"

            now = datetime.now()
            tanggal = now.strftime("%Y-%m-%d")
            waktu = now.strftime("%H:%M")

            cur.execute(
                """INSERT INTO transaksi
                   (id, tanggal, waktu, subtotal, diskon_nominal, diskon_id, total, metode,
                    kasir_username, nama_customer, email_customer)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (trx_id, tanggal, waktu, subtotal, diskon_nominal, diskon_id, total, metode,
                 g.user["username"], nama_customer, email_customer),
            )

            stok_menipis_list = []
            for it in items:
                cur.execute(
                    """INSERT INTO transaksi_items (transaksi_id, kode_produk, nama, harga, qty, subtotal)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (trx_id, it["kode"], it["nama"], it["harga"], it["qty"], it["subtotal"]),
                )
                cur.execute("SELECT * FROM produk WHERE kode=%s FOR UPDATE", (it["kode"],))
                p = cur.fetchone()
                if p:
                    new_stok = max(0, p["stok"] - it["qty"])
                    cur.execute("UPDATE produk SET stok=%s WHERE kode=%s", (new_stok, it["kode"]))
                    if new_stok <= THRESHOLD:
                        p = dict(p)
                        p["stok"] = new_stok
                        stok_menipis_list.append(p)
        conn.commit()
    except Exception as err:
        conn.rollback()
        return jsonify({"message": f"Gagal menyimpan transaksi: {err}"}), 500
    finally:
        conn.autocommit(True)

    try:
        create_notifikasi(
            target_role="admin", tipe="transaksi_baru", judul="Transaksi Baru",
            pesan=f"{trx_id} sebesar Rp{total:,} oleh {g.user['username']}.".replace(",", "."),
            ref_kode=trx_id,
        )
    except Exception:
        pass

    if email_customer:
        try:
            result = send_struk_email({
                "id": trx_id, "tanggal": tanggal, "waktu": waktu, "items": items,
                "subtotal": subtotal, "diskon_nominal": diskon_nominal, "total": total,
                "metode": metode, "kasir_username": g.user["username"], "email_customer": email_customer,
            })
            if result.get("ok"):
                query("UPDATE transaksi SET struk_terkirim=1 WHERE id=%s", (trx_id,), fetch=None)
        except Exception:
            pass

    for p in stok_menipis_list:
        try:
            create_notifikasi(
                target_role="admin",
                tipe="stok_habis" if p["stok"] == 0 else "stok_menipis",
                judul="Stok Habis" if p["stok"] == 0 else "Stok Menipis",
                pesan=f"Stok \"{p['nama']}\" ({p['kode']}) tersisa {p['stok']} unit setelah transaksi {trx_id}.",
                ref_kode=p["kode"],
            )
        except Exception:
            pass
    if stok_menipis_list:
        try:
            send_stok_menipis_email(stok_menipis_list)
        except Exception:
            pass

    return jsonify({
        "message": "Transaksi berhasil disimpan.",
        "transaksi": {
            "id": trx_id, "tanggal": tanggal, "waktu": waktu, "items": items,
            "subtotal": subtotal, "diskon_nominal": diskon_nominal, "total": total, "metode": metode,
        },
    }), 201
