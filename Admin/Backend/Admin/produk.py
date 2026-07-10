"""
F002-F004: CRUD Produk + Manajemen Stok + upload foto Cloudinary
+ Notifikasi kasir untuk produk baru/update/hapus/stok menipis/habis.
"""

from flask import Blueprint, request, jsonify

from db_conn import query
from Backend.Utils.auth import auth_required, require_role
from Backend.Utils.cloudinary_util import upload_image, delete_image
from Backend.Utils.resend_util import send_stok_menipis_email
from Backend.Utils.notify import (
    create_notifikasi,
    notif_produk_kasir,
    notif_stok_berubah,
    notif_stok_langsung,
)

bp = Blueprint("produk", __name__, url_prefix="/api/produk")

THRESHOLD = 8
PREFIX_MAP = {
    "Kopi": "KP",
    "Non-Kopi": "NK",
    "Makanan": "MK",
    "Snack": "SN",
}


def _safe_notify(func, *args):
    """
    Supaya proses utama produk tidak gagal hanya karena notifikasi/email gagal.
    """
    try:
        func(*args)
    except Exception as err:
        print(f"[Notifikasi] Gagal menjalankan {func.__name__}: {err}")


def _parse_int(value, field_name):
    try:
        angka = int(value)
        if angka < 0:
            return None, f"{field_name} tidak boleh kurang dari 0."
        return angka, None
    except (TypeError, ValueError):
        return None, f"{field_name} tidak valid."


def _next_kode(kategori, offset=1):
    """
    Membuat kode produk otomatis berdasarkan kategori.
    Dibuat lebih aman agar tidak duplicate key.
    """
    prefix = PREFIX_MAP.get(kategori, "PR")

    rows = query(
        "SELECT kode FROM produk WHERE kode LIKE %s",
        (f"{prefix}-%",),
    )

    nums = []

    for row in rows:
        try:
            nums.append(int(str(row["kode"]).split("-")[-1]))
        except (IndexError, ValueError, TypeError):
            pass

    last_num = max(nums) if nums else 0
    return f"{prefix}-{last_num + offset:03d}"


def _generate_unique_kode(kategori):
    """
    Cek kode satu per satu supaya tidak bentrok dengan kode yang sudah ada.
    """
    for offset in range(1, 1000):
        calon_kode = _next_kode(kategori, offset)

        existing = query(
            "SELECT kode FROM produk WHERE kode=%s",
            (calon_kode,),
            fetch="one",
        )

        if not existing:
            return calon_kode

    raise Exception("Gagal membuat kode produk unik.")


def _check_and_notify_stok_admin(produk, stok_lama=None):
    """
    Notifikasi stok untuk admin + email admin.
    Dibuat tidak terlalu spam:
    - stok baru habis dari sebelumnya masih ada
    - stok baru masuk batas menipis dari sebelumnya aman
    """
    if not produk:
        return

    try:
        stok_baru = int(produk.get("stok") or 0)
    except Exception:
        return

    stok_lama_int = None

    if stok_lama is not None:
        try:
            stok_lama_int = int(stok_lama or 0)
        except Exception:
            stok_lama_int = None

    should_notify = False

    if stok_lama_int is None:
        should_notify = stok_baru <= THRESHOLD
    else:
        if stok_baru == 0 and stok_lama_int > 0:
            should_notify = True
        elif stok_baru <= THRESHOLD and stok_lama_int > THRESHOLD:
            should_notify = True

    if not should_notify:
        return

    if stok_baru == 0:
        create_notifikasi(
            target_role="admin",
            tipe="stok_habis",
            judul="Stok Habis",
            pesan=f"Stok \"{produk['nama']}\" ({produk['kode']}) telah habis.",
            ref_kode=produk["kode"],
        )
    else:
        create_notifikasi(
            target_role="admin",
            tipe="stok_menipis",
            judul="Stok Menipis",
            pesan=f"Stok \"{produk['nama']}\" ({produk['kode']}) tersisa {stok_baru} unit.",
            ref_kode=produk["kode"],
        )

    try:
        send_stok_menipis_email([produk])
    except Exception as err:
        print(f"[Resend] Gagal kirim email stok: {err}")


@bp.get("")
@auth_required
def list_produk():
    rows = query("SELECT * FROM produk ORDER BY created_at DESC")
    return jsonify({"produk": rows})


@bp.post("")
@auth_required
@require_role("admin")
def add_produk():
    data = request.get_json(silent=True) or {}

    nama = (data.get("nama") or "").strip()
    kategori = data.get("kategori")
    harga = data.get("harga")
    stok = data.get("stok")
    status = data.get("status") or "Aktif"

    if not nama or not kategori or harga is None or stok is None:
        return jsonify({
            "message": "Nama, kategori, harga, dan stok wajib diisi."
        }), 400

    harga, err = _parse_int(harga, "Harga")
    if err:
        return jsonify({"message": err}), 400

    stok, err = _parse_int(stok, "Stok")
    if err:
        return jsonify({"message": err}), 400

    try:
        kode = _generate_unique_kode(kategori)
    except Exception as err:
        return jsonify({"message": str(err)}), 500

    query(
        """
        INSERT INTO produk (kode, nama, kategori, harga, stok, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (kode, nama, kategori, harga, stok, status),
        fetch=None,
    )

    row = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    # Notifikasi ke kasir: produk baru
    _safe_notify(
        notif_produk_kasir,
        "produk_baru",
        row["kode"],
        row["nama"],
    )

    # Notifikasi ke kasir kalau stok awal langsung menipis/habis
    _safe_notify(
        notif_stok_langsung,
        row["kode"],
        row["nama"],
        row["stok"],
    )

    # Notifikasi admin + email admin kalau stok menipis/habis
    _safe_notify(
        _check_and_notify_stok_admin,
        row,
    )

    return jsonify({
        "message": "Produk baru berhasil ditambahkan.",
        "produk": row,
    }), 201


@bp.put("/<kode>")
@auth_required
@require_role("admin")
def update_produk(kode):
    old = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    if not old:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    data = request.get_json(silent=True) or {}

    nama = data.get("nama", old["nama"])
    kategori = data.get("kategori", old["kategori"])
    harga = data.get("harga", old["harga"])
    stok = data.get("stok", old["stok"])
    status = data.get("status", old["status"])

    nama = (nama or "").strip()

    if not nama or not kategori or harga is None or stok is None:
        return jsonify({
            "message": "Nama, kategori, harga, dan stok wajib diisi."
        }), 400

    harga, err = _parse_int(harga, "Harga")
    if err:
        return jsonify({"message": err}), 400

    stok, err = _parse_int(stok, "Stok")
    if err:
        return jsonify({"message": err}), 400

    query(
        """
        UPDATE produk
        SET nama=%s,
            kategori=%s,
            harga=%s,
            stok=%s,
            status=%s
        WHERE kode=%s
        """,
        (nama, kategori, harga, stok, status, kode),
        fetch=None,
    )

    row = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    if not row:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    # Notifikasi ke kasir: produk diupdate
    _safe_notify(
        notif_produk_kasir,
        "produk_update",
        row["kode"],
        row["nama"],
    )

    # Notifikasi ke kasir kalau stok berubah menjadi menipis/habis
    _safe_notify(
        notif_stok_berubah,
        row["kode"],
        row["nama"],
        old["stok"],
        row["stok"],
    )

    # Notifikasi admin + email admin kalau stok menipis/habis
    _safe_notify(
        _check_and_notify_stok_admin,
        row,
        old["stok"],
    )

    return jsonify({
        "message": "Perubahan produk berhasil disimpan.",
        "produk": row,
    })


@bp.delete("/<kode>")
@auth_required
@require_role("admin")
def delete_produk(kode):
    old = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    if not old:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    if old.get("foto_public_id"):
        try:
            delete_image(old["foto_public_id"])
        except Exception as err:
            print(f"[Cloudinary] Gagal hapus foto produk: {err}")

    query(
        "DELETE FROM produk WHERE kode=%s",
        (kode,),
        fetch=None,
    )

    # Notifikasi ke kasir: produk dihapus
    _safe_notify(
        notif_produk_kasir,
        "produk_hapus",
        old["kode"],
        old["nama"],
    )

    return jsonify({"message": "Produk berhasil dihapus."})


@bp.post("/<kode>/stok")
@auth_required
@require_role("admin")
def update_stok(kode):
    data = request.get_json(silent=True) or {}

    mode = data.get("mode")
    jumlah = data.get("jumlah")

    old = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    if not old:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    jumlah, err = _parse_int(jumlah, "Jumlah")
    if err:
        return jsonify({"message": err}), 400

    if mode == "tambah":
        stok_baru = int(old["stok"]) + jumlah

    elif mode == "kurangi":
        stok_baru = max(0, int(old["stok"]) - jumlah)

    elif mode == "set":
        stok_baru = max(0, jumlah)

    else:
        return jsonify({"message": "Mode tidak dikenali."}), 400

    query(
        "UPDATE produk SET stok=%s WHERE kode=%s",
        (stok_baru, kode),
        fetch=None,
    )

    updated = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    # Notifikasi ke kasir: stok/produk diperbarui
    _safe_notify(
        notif_produk_kasir,
        "produk_update",
        updated["kode"],
        updated["nama"],
    )

    # Notifikasi ke kasir kalau stok berubah menjadi menipis/habis
    _safe_notify(
        notif_stok_berubah,
        updated["kode"],
        updated["nama"],
        old["stok"],
        updated["stok"],
    )

    # Notifikasi admin + email admin kalau stok menipis/habis
    _safe_notify(
        _check_and_notify_stok_admin,
        updated,
        old["stok"],
    )

    return jsonify({
        "message": "Stok produk berhasil diperbarui.",
        "produk": updated,
    })


@bp.post("/<kode>/foto")
@auth_required
@require_role("admin")
def upload_foto_produk(kode):
    if "foto" not in request.files:
        return jsonify({"message": "File foto tidak ditemukan."}), 400

    old = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    if old is None:
        return jsonify({"message": "Produk tidak ditemukan."}), 404

    try:
        result = upload_image(request.files["foto"], "antari/produk")
    except Exception as err:
        return jsonify({
            "message": f"Gagal mengunggah foto produk: {err}"
        }), 500

    if old.get("foto_public_id"):
        try:
            delete_image(old["foto_public_id"])
        except Exception as err:
            print(f"[Cloudinary] Gagal hapus foto lama: {err}")

    query(
        """
        UPDATE produk
        SET foto_url=%s,
            foto_public_id=%s
        WHERE kode=%s
        """,
        (result["url"], result["public_id"], kode),
        fetch=None,
    )

    row = query(
        "SELECT * FROM produk WHERE kode=%s",
        (kode,),
        fetch="one",
    )

    # Notifikasi ke kasir: produk diperbarui karena foto berubah
    if row:
        _safe_notify(
            notif_produk_kasir,
            "produk_update",
            row["kode"],
            row["nama"],
        )

    return jsonify({
        "message": "Foto produk berhasil diperbarui.",
        "foto_url": result["url"],
    })