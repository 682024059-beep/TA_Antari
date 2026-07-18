"""
Profil pengguna — dipakai admin maupun kasir.
Password lama/baru TIDAK PERNAH dikembalikan dalam response apa pun.
"""
import bcrypt
from flask import Blueprint, request, jsonify, g
from db_conn import query
from Backend.Utils.auth import auth_required
from Backend.Utils.cloudinary_util import upload_image
from Backend.Utils.resend_util import send_password_changed_email

bp = Blueprint("profil", __name__, url_prefix="/api/profil")


@bp.get("")
@auth_required
def get_profil():
    row = query(
        "SELECT id, username, nama, role, email, foto_url, created_at FROM users WHERE id=%s",
        (g.user["id"],), fetch="one",
    )
    if not row:
        return jsonify({"message": "Profil tidak ditemukan."}), 404
    return jsonify({"profil": row})


@bp.put("")
@auth_required
def update_profil():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    nama = (data.get("nama") or "").strip()
    email = data.get("email")

    if email:
        email = str(email).strip()
    else:
        email = None

    if not username:
        return jsonify({"message": "Username tidak boleh kosong."}), 400

    if " " in username:
        return jsonify({"message": "Username tidak boleh mengandung spasi."}), 400

    if not nama:
        return jsonify({"message": "Nama tidak boleh kosong."}), 400

    existing = query(
        """
        SELECT id
        FROM users
        WHERE id <> %s
          AND (
                username = %s
                OR (
                    email IS NOT NULL
                    AND email <> ''
                    AND email = %s
                )
              )
        LIMIT 1
        """,
        (g.user["id"], username, email),
        fetch="one",
    )

    if existing:
        return jsonify({
            "message": "Username atau email sudah digunakan akun lain."
        }), 409

    query(
        """
        UPDATE users
        SET
            username = %s,
            nama = %s,
            email = %s
        WHERE id = %s
        """,
        (
            username,
            nama,
            email,
            g.user["id"],
        ),
        fetch=None,
    )

    row = query(
        """
        SELECT
            id,
            username,
            nama,
            role,
            email,
            foto_url
        FROM users
        WHERE id = %s
        """,
        (g.user["id"],),
        fetch="one",
    )

    return jsonify({
        "message": "Profil berhasil diperbarui.",
        "profil": row
    })


@bp.post("/ganti-password")
@auth_required
def ganti_password():
    data = request.get_json(silent=True) or {}
    password_lama = data.get("passwordLama")
    password_baru = data.get("passwordBaru")

    if not password_lama or not password_baru:
        return jsonify({"message": "Password lama dan password baru wajib diisi."}), 400
    if len(password_baru) < 6:
        return jsonify({"message": "Password baru minimal 6 karakter."}), 400

    row = query("SELECT password_hash, email, nama FROM users WHERE id=%s", (g.user["id"],), fetch="one")
    if not row:
        return jsonify({"message": "Akun tidak ditemukan."}), 404

    if not bcrypt.checkpw(password_lama.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return jsonify({"message": "Password lama tidak sesuai."}), 401

    new_hash = bcrypt.hashpw(password_baru.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    query("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, g.user["id"]), fetch=None)

    try:
        send_password_changed_email(row["email"], row["nama"])
    except Exception:
        pass

    return jsonify({"message": "Password berhasil diperbarui."})


@bp.post("/foto")
@auth_required
def upload_foto_profil():
    if "foto" not in request.files:
        return jsonify({"message": "File foto tidak ditemukan."}), 400
    file = request.files["foto"]
    try:
        result = upload_image(file, "antari/profil")
    except Exception as err:
        return jsonify({"message": f"Gagal mengunggah foto profil: {err}"}), 500

    query("UPDATE users SET foto_url=%s WHERE id=%s", (result["url"], g.user["id"]), fetch=None)
    return jsonify({"message": "Foto profil berhasil diperbarui.", "foto_url": result["url"]})
