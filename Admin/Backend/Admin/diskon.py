"""
F005: CRUD Diskon
"""

from flask import Blueprint, request, jsonify
from db_conn import query
from Backend.Utils.auth import auth_required, require_role
from Backend.Utils.notify import create_notifikasi

bp = Blueprint("diskon", __name__, url_prefix="/api/diskon")


def _clean(value):
    return str(value or "").strip()


def _next_id():
    rows = query("SELECT id FROM diskon")
    nums = []

    for r in rows:
        try:
            nums.append(int(str(r["id"]).split("-")[1]))
        except (IndexError, ValueError, KeyError):
            pass

    nxt = (max(nums) if nums else 0) + 1
    return f"D-{nxt:03d}"


def _format_nilai_diskon(jenis, nilai):
    try:
        nilai_int = int(nilai)
    except (TypeError, ValueError):
        nilai_int = 0

    if jenis == "Persen":
        return f"{nilai_int}%"

    return f"Rp {nilai_int:,}".replace(",", ".")


def _is_nonaktif(status):
    status_clean = _clean(status).lower()

    return status_clean in [
        "nonaktif",
        "tidak aktif",
        "inactive",
        "mati",
        "0",
        "false",
    ]


def _is_aktif(status):
    status_clean = _clean(status).lower()

    return status_clean in [
        "aktif",
        "active",
        "1",
        "true",
    ]

def _ambil_status_dari_payload(data, old_row=None):
    """
    Membaca status dari berbagai kemungkinan kiriman frontend.
    Supaya kalau frontend kirim:
    - status: "Nonaktif"
    - is_active: false
    - aktif: false
    tetap dianggap Nonaktif.
    """

    if "status" in data:
        status = _clean(data.get("status"))

        if status:
            return status

    if "is_active" in data:
        value = data.get("is_active")

        if value in [False, 0, "0", "false", "False", "nonaktif", "Nonaktif"]:
            return "Nonaktif"

        return "Aktif"

    if "aktif" in data:
        value = data.get("aktif")

        if value in [False, 0, "0", "false", "False", "nonaktif", "Nonaktif"]:
            return "Nonaktif"

        return "Aktif"

    if old_row:
        return _clean(old_row.get("status")) or "Aktif"

    return "Aktif"


def _safe_create_notifikasi(
    target_role="kasir",
    tipe="diskon",
    judul="Notifikasi Diskon",
    pesan="",
    ref_kode=None,
):
    """
    Supaya proses CRUD diskon tetap berhasil meskipun insert notifikasi bermasalah.
    """
    try:
        create_notifikasi(
            target_role=target_role,
            tipe=tipe,
            judul=judul,
            pesan=pesan,
            ref_kode=ref_kode,
        )
    except Exception as err:
        print(f"[NOTIF DISKON ERROR] {err}")


def _kirim_notifikasi_diskon_baru(diskon_id, nama, jenis, nilai, status):
    nilai_text = _format_nilai_diskon(jenis, nilai)

    if _is_nonaktif(status):
        _safe_create_notifikasi(
            target_role="kasir",
            tipe="diskon_nonaktif",
            judul="Diskon Baru Nonaktif",
            pesan=f'Diskon "{nama}" sebesar {nilai_text} ditambahkan oleh admin, tetapi statusnya nonaktif dan belum berlaku di kasir.',
            ref_kode=diskon_id,
        )
        return

    _safe_create_notifikasi(
        target_role="kasir",
        tipe="diskon_baru",
        judul="Diskon Baru",
        pesan=f'Diskon "{nama}" sebesar {nilai_text} telah ditambahkan oleh admin dan sudah berlaku di kasir.',
        ref_kode=diskon_id,
    )


def _kirim_notifikasi_diskon_update(diskon_id, old_row, nama, jenis, nilai, status):
    nilai_text = _format_nilai_diskon(jenis, nilai)

    old_status = old_row.get("status") or "Aktif"
    old_nonaktif = _is_nonaktif(old_status)
    new_nonaktif = _is_nonaktif(status)

    # Kalau status baru nonaktif, jangan tampilkan "Diskon Diperbarui"
    if new_nonaktif:
        _safe_create_notifikasi(
            target_role="kasir",
            tipe="diskon_nonaktif",
            judul="Diskon Dinonaktifkan",
            pesan=f'Diskon "{nama}" telah dinonaktifkan oleh admin dan tidak berlaku di kasir.',
            ref_kode=diskon_id,
        )
        return

    # Kalau sebelumnya nonaktif lalu sekarang aktif
    if old_nonaktif and _is_aktif(status):
        _safe_create_notifikasi(
            target_role="kasir",
            tipe="diskon_aktif",
            judul="Diskon Diaktifkan",
            pesan=f'Diskon "{nama}" telah diaktifkan oleh admin. Nilai diskon saat ini {nilai_text}.',
            ref_kode=diskon_id,
        )
        return

    # Kalau status tetap aktif, baru tampilkan update biasa
    _safe_create_notifikasi(
        target_role="kasir",
        tipe="diskon_update",
        judul="Diskon Diperbarui",
        pesan=f'Diskon "{nama}" telah diperbarui oleh admin. Nilai diskon sekarang {nilai_text}.',
        ref_kode=diskon_id,
    )


@bp.get("")
@auth_required
def list_diskon():
    rows = query("SELECT * FROM diskon ORDER BY created_at DESC")
    return jsonify({"diskon": rows})


@bp.post("")
@auth_required
@require_role("admin")
def add_diskon():
    data = request.get_json(silent=True) or {}

    nama = _clean(data.get("nama"))
    jenis = data.get("jenis")
    nilai = data.get("nilai")
    mulai = data.get("mulai")
    selesai = data.get("selesai")
    status = _clean(data.get("status")) or "Aktif"

    if not nama or not jenis or nilai is None or not mulai or not selesai:
        return jsonify({
            "message": "Semua field diskon wajib diisi."
        }), 400

    diskon_id = _next_id()

    query(
        """
        INSERT INTO diskon (
            id,
            nama,
            jenis,
            nilai,
            mulai,
            selesai,
            status
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            diskon_id,
            nama,
            jenis,
            nilai,
            mulai,
            selesai,
            status,
        ),
        fetch=None,
    )

    _kirim_notifikasi_diskon_baru(
        diskon_id=diskon_id,
        nama=nama,
        jenis=jenis,
        nilai=nilai,
        status=status,
    )

    row = query(
        "SELECT * FROM diskon WHERE id=%s",
        (diskon_id,),
        fetch="one",
    )

    return jsonify({
        "message": "Diskon baru berhasil ditambahkan.",
        "diskon": row,
    }), 201


@bp.put("/<diskon_id>")
@auth_required
@require_role("admin")
def update_diskon(diskon_id):
    data = request.get_json(silent=True) or {}

    old_row = query(
        "SELECT * FROM diskon WHERE id=%s",
        (diskon_id,),
        fetch="one",
    )

    if not old_row:
        return jsonify({
            "message": "Diskon tidak ditemukan."
        }), 404

    nama = _clean(data.get("nama") or old_row.get("nama"))
    jenis = data.get("jenis") or old_row.get("jenis")
    nilai = data.get("nilai") if data.get("nilai") is not None else old_row.get("nilai")
    mulai = data.get("mulai") or old_row.get("mulai")
    selesai = data.get("selesai") or old_row.get("selesai")
    status = _ambil_status_dari_payload(data, old_row)

    if not nama or not jenis or nilai is None or not mulai or not selesai:
        return jsonify({
            "message": "Semua field diskon wajib diisi."
        }), 400

    query(
        """
        UPDATE diskon
        SET
            nama=%s,
            jenis=%s,
            nilai=%s,
            mulai=%s,
            selesai=%s,
            status=%s
        WHERE id=%s
        """,
        (
            nama,
            jenis,
            nilai,
            mulai,
            selesai,
            status,
            diskon_id,
        ),
        fetch=None,
    )

    _kirim_notifikasi_diskon_update(
        diskon_id=diskon_id,
        old_row=old_row,
        nama=nama,
        jenis=jenis,
        nilai=nilai,
        status=status,
    )

    row = query(
        "SELECT * FROM diskon WHERE id=%s",
        (diskon_id,),
        fetch="one",
    )

    return jsonify({
        "message": "Perubahan diskon berhasil disimpan.",
        "diskon": row,
    })


@bp.delete("/<diskon_id>")
@auth_required
@require_role("admin")
def delete_diskon(diskon_id):
    row = query(
        "SELECT * FROM diskon WHERE id=%s",
        (diskon_id,),
        fetch="one",
    )

    if not row:
        return jsonify({
            "message": "Diskon tidak ditemukan."
        }), 404

    nama = row.get("nama", "Diskon")

    query(
        "DELETE FROM diskon WHERE id=%s",
        (diskon_id,),
        fetch=None,
    )

    _safe_create_notifikasi(
        target_role="kasir",
        tipe="diskon_hapus",
        judul="Diskon Dihapus",
        pesan=f'Diskon "{nama}" telah dihapus oleh admin dan tidak tersedia di kasir.',
        ref_kode=diskon_id,
    )

    return jsonify({
        "message": "Diskon berhasil dihapus."
    })