"""
F001 Login Sistem — autentikasi via MySQL + bcrypt + JWT.
Endpoint ini TIDAK PERNAH mengembalikan password/hash apa pun.
"""
import bcrypt
from flask import Blueprint, request, jsonify, g
from db_conn import query
from Backend.Utils.auth import generate_token, auth_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"message": "Username dan password wajib diisi."}), 400

    user = query(
        "SELECT id, username, password_hash, nama, role, email, foto_url, is_active FROM users WHERE username=%s",
        (username,),
        fetch="one",
    )
    if not user or not user["is_active"]:
        return jsonify({"message": "Username atau password salah. Silakan periksa kembali."}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"message": "Username atau password salah. Silakan periksa kembali."}), 401

    token = generate_token({
        "id": user["id"], "username": user["username"], "nama": user["nama"], "role": user["role"],
    })

    # password_hash sengaja tidak pernah dikirim ke frontend
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"], "username": user["username"], "nama": user["nama"],
            "role": user["role"], "email": user["email"], "foto_url": user["foto_url"],
        },
    })


@bp.get("/me")
@auth_required
def me():
    row = query(
        "SELECT id, username, nama, role, email, foto_url FROM users WHERE id=%s",
        (g.user["id"],), fetch="one",
    )
    if not row:
        return jsonify({"message": "Akun tidak ditemukan."}), 404
    return jsonify({"user": row})
