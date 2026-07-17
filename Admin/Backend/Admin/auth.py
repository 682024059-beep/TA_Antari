"""
F001 Login Sistem — autentikasi via MySQL + bcrypt + JWT.
Endpoint ini TIDAK PERNAH mengembalikan password/hash apa pun.

Update:
- Login admin memakai email dan password.
- Mendukung forgot password dan reset password via email.
"""

import bcrypt
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, g

from db_conn import query
from config import Config
from Backend.Utils.auth import generate_token, auth_required
from Backend.Utils.resend_util import send_reset_password_email

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _safe_user_response(user):
    """Data user yang aman dikirim ke frontend."""
    return {
        "id": user["id"],
        "username": user["username"],
        "nama": user["nama"],
        "role": user["role"],
        "email": user["email"],
        "foto_url": user["foto_url"],
    }


def _find_user_by_email(email):
    """
    Mencari user berdasarkan email.
    Email dibuat lowercase agar tidak terpengaruh huruf kapital saat login.
    """
    email = (email or "").strip().lower()

    return query(
        """
        SELECT id, username, password_hash, nama, role, email, foto_url, is_active
        FROM users
        WHERE LOWER(TRIM(email)) = %s
        LIMIT 1
        """,
        (email,),
        fetch="one",
    )

def _get_app_base_url():
    """
    Mengambil base URL aplikasi.
    Jika APP_BASE_URL di env sudah diisi, gunakan itu.
    Jika belum, ambil otomatis dari request host Vercel.
    """

    env_base_url = getattr(Config, "APP_BASE_URL", "") or ""
    env_base_url = env_base_url.strip().rstrip("/")

    if env_base_url and "localhost" not in env_base_url and "127.0.0.1" not in env_base_url:
        return env_base_url

    forwarded_proto = request.headers.get("X-Forwarded-Proto")
    forwarded_host = request.headers.get("X-Forwarded-Host")

    proto = forwarded_proto or request.scheme or "https"
    host = forwarded_host or request.host

    if host and "localhost" not in host and "127.0.0.1" not in host:
        return f"{proto}://{host}".rstrip("/")

    return env_base_url or "http://localhost:4000"


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email dan password wajib diisi."}), 400

    user = _find_user_by_email(email)

    if not user or not user["is_active"]:
        return jsonify({
            "message": "Email atau password salah. Silakan periksa kembali."
        }), 401

    password_hash = user["password_hash"]

    if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
        return jsonify({
            "message": "Email atau password salah. Silakan periksa kembali."
        }), 401

    token = generate_token({
        "id": user["id"],
        "username": user["username"],
        "nama": user["nama"],
        "role": user["role"],
        "email": user["email"],
    })

    return jsonify({
        "token": token,
        "user": _safe_user_response(user),
    })

@bp.post("/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "Email wajib diisi."}), 400

    user = query(
        """
        SELECT id, username, nama, role, email, is_active
        FROM users
        WHERE LOWER(email) = %s
        LIMIT 1
        """,
        (email,),
        fetch="one",
    )

    success_message = "Jika email terdaftar, link reset password akan dikirim."

    if not user or not user["is_active"]:
        return jsonify({"message": success_message}), 200

    reset_token = secrets.token_urlsafe(32)
    reset_expired = datetime.now() + timedelta(minutes=30)

    query(
        """
        UPDATE users
        SET reset_token = %s,
            reset_expired = %s
        WHERE id = %s
        """,
        (
            reset_token,
            reset_expired.strftime("%Y-%m-%d %H:%M:%S"),
            user["id"],
        ),
        fetch=None,
    )

    app_base_url = _get_app_base_url()
    reset_link = f"{app_base_url}/admin/reset-password.html?token={reset_token}"

    try:
        send_reset_password_email(
            to_email=user["email"],
            nama=user["nama"],
            reset_link=reset_link,
        )
    except Exception:
        pass

    return jsonify({"message": success_message}), 200


@bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}

    token = (data.get("token") or "").strip()
    password_baru = data.get("password") or ""

    if not token or not password_baru:
        return jsonify({"message": "Token dan password baru wajib diisi."}), 400

    if len(password_baru) < 6:
        return jsonify({"message": "Password baru minimal 6 karakter."}), 400

    user = query(
        """
        SELECT id, username, nama, email, reset_token, reset_expired
        FROM users
        WHERE reset_token = %s
        LIMIT 1
        """,
        (token,),
        fetch="one",
    )

    if not user:
        return jsonify({"message": "Link reset password tidak valid."}), 400

    expired = user["reset_expired"]

    if expired:
        if isinstance(expired, str):
            try:
                expired_dt = datetime.fromisoformat(expired)
            except ValueError:
                expired_dt = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
        else:
            expired_dt = expired

        if expired_dt < datetime.now():
            return jsonify({"message": "Link reset password sudah kedaluwarsa."}), 400

    new_hash = bcrypt.hashpw(
        password_baru.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    query(
        """
        UPDATE users
        SET password_hash = %s,
            reset_token = NULL,
            reset_expired = NULL
        WHERE id = %s
        """,
        (new_hash, user["id"]),
        fetch=None,
    )

    return jsonify({
        "message": "Password berhasil direset. Silakan login dengan password baru."
    }), 200


@bp.get("/me")
@auth_required
def me():
    row = query(
        """
        SELECT id, username, nama, role, email, foto_url
        FROM users
        WHERE id = %s
        """,
        (g.user["id"],),
        fetch="one",
    )

    if not row:
        return jsonify({"message": "Akun tidak ditemukan."}), 404

    return jsonify({"user": row})