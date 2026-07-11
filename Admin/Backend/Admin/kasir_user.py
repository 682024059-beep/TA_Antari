"""
CRUD Akun Kasir
Dipakai admin untuk membuat, edit, reset password, dan nonaktifkan akun kasir.

Catatan:
- Tabel users memakai id BIGINT AUTO_INCREMENT.
- Jadi INSERT tidak boleh memakai UUID() dan tidak boleh mengisi kolom id.
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from db_conn import query

bp = Blueprint("kasir_user", __name__, url_prefix="/api/kasir-users")


def _clean(value):
    return str(value or "").strip()


def _status_to_active(status):
    return 1 if str(status or "").strip().lower() == "aktif" else 0


@bp.get("")
@bp.get("/")
def list_kasir_users():
    rows = query(
        """
        SELECT
            id,
            nama,
            username,
            email,
            role,
            status,
            is_active,
            created_at,
            updated_at
        FROM users
        WHERE role = 'kasir'
        ORDER BY created_at DESC
        """
    )

    return jsonify({"kasir": rows})


@bp.post("")
@bp.post("/")
def add_kasir_user():
    data = request.get_json(silent=True) or {}

    nama = _clean(data.get("nama"))
    username = _clean(data.get("username"))
    email = _clean(data.get("email"))
    password = _clean(data.get("password"))
    status = _clean(data.get("status")) or "Aktif"

    if not nama or not username or not password:
        return jsonify({
            "message": "Nama, username, dan password wajib diisi."
        }), 400

    if " " in username:
        return jsonify({
            "message": "Username tidak boleh mengandung spasi."
        }), 400

    if len(password) < 6:
        return jsonify({
            "message": "Password minimal 6 karakter."
        }), 400

    existing = query(
        """
        SELECT id
        FROM users
        WHERE username = %s
           OR (email IS NOT NULL AND email <> '' AND email = %s)
        LIMIT 1
        """,
        (username, email),
        fetch="one",
    )

    if existing:
        return jsonify({
            "message": "Username atau email sudah digunakan."
        }), 409

    password_hash = generate_password_hash(password)
    is_active = _status_to_active(status)

    # PENTING:
    # id tidak dimasukkan karena id users adalah BIGINT AUTO_INCREMENT.
    query(
        """
        INSERT INTO users
        (
            username,
            password_hash,
            nama,
            role,
            email,
            status,
            is_active
        )
        VALUES
        (
            %s,
            %s,
            %s,
            'kasir',
            %s,
            %s,
            %s
        )
        """,
        (
            username,
            password_hash,
            nama,
            email or None,
            status,
            is_active,
        ),
        fetch=None,
    )

    row = query(
        """
        SELECT
            id,
            nama,
            username,
            email,
            role,
            status,
            is_active,
            created_at,
            updated_at
        FROM users
        WHERE username = %s
        LIMIT 1
        """,
        (username,),
        fetch="one",
    )

    return jsonify({
        "message": "Akun kasir berhasil dibuat.",
        "kasir": row,
    }), 201


@bp.put("/<int:user_id>")
def update_kasir_user(user_id):
    data = request.get_json(silent=True) or {}

    nama = _clean(data.get("nama"))
    username = _clean(data.get("username"))
    email = _clean(data.get("email"))
    status = _clean(data.get("status")) or "Aktif"

    if not nama or not username:
        return jsonify({
            "message": "Nama dan username wajib diisi."
        }), 400

    if " " in username:
        return jsonify({
            "message": "Username tidak boleh mengandung spasi."
        }), 400

    old = query(
        """
        SELECT id
        FROM users
        WHERE id = %s
          AND role = 'kasir'
        LIMIT 1
        """,
        (user_id,),
        fetch="one",
    )

    if not old:
        return jsonify({
            "message": "Akun kasir tidak ditemukan."
        }), 404

    existing = query(
        """
        SELECT id
        FROM users
        WHERE id <> %s
          AND (
                username = %s
                OR (email IS NOT NULL AND email <> '' AND email = %s)
              )
        LIMIT 1
        """,
        (user_id, username, email),
        fetch="one",
    )

    if existing:
        return jsonify({
            "message": "Username atau email sudah digunakan akun lain."
        }), 409

    is_active = _status_to_active(status)

    query(
        """
        UPDATE users
        SET
            nama = %s,
            username = %s,
            email = %s,
            status = %s,
            is_active = %s
        WHERE id = %s
          AND role = 'kasir'
        """,
        (
            nama,
            username,
            email or None,
            status,
            is_active,
            user_id,
        ),
        fetch=None,
    )

    row = query(
        """
        SELECT
            id,
            nama,
            username,
            email,
            role,
            status,
            is_active,
            created_at,
            updated_at
        FROM users
        WHERE id = %s
        LIMIT 1
        """,
        (user_id,),
        fetch="one",
    )

    return jsonify({
        "message": "Akun kasir berhasil diperbarui.",
        "kasir": row,
    })


@bp.patch("/<int:user_id>/password")
def reset_password_kasir(user_id):
    data = request.get_json(silent=True) or {}
    password = _clean(data.get("password"))

    if not password:
        return jsonify({
            "message": "Password baru wajib diisi."
        }), 400

    if len(password) < 6:
        return jsonify({
            "message": "Password minimal 6 karakter."
        }), 400

    old = query(
        """
        SELECT id
        FROM users
        WHERE id = %s
          AND role = 'kasir'
        LIMIT 1
        """,
        (user_id,),
        fetch="one",
    )

    if not old:
        return jsonify({
            "message": "Akun kasir tidak ditemukan."
        }), 404

    password_hash = generate_password_hash(password)

    query(
        """
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
          AND role = 'kasir'
        """,
        (password_hash, user_id),
        fetch=None,
    )

    return jsonify({
        "message": "Password kasir berhasil direset."
    })


@bp.delete("/<int:user_id>")
def nonaktifkan_kasir(user_id):
    old = query(
        """
        SELECT id
        FROM users
        WHERE id = %s
          AND role = 'kasir'
        LIMIT 1
        """,
        (user_id,),
        fetch="one",
    )

    if not old:
        return jsonify({
            "message": "Akun kasir tidak ditemukan."
        }), 404

    query(
        """
        UPDATE users
        SET
            status = 'Nonaktif',
            is_active = 0
        WHERE id = %s
          AND role = 'kasir'
        """,
        (user_id,),
        fetch=None,
    )

    return jsonify({
        "message": "Akun kasir berhasil dinonaktifkan."
    })