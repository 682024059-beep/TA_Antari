"""
Autentikasi JWT untuk Flask.
Token dikirim frontend lewat header: Authorization: Bearer <token>
"""

import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, g
from config import Config


def no_cache_response(response):
    """
    Mencegah response auth disimpan cache browser.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def generate_token(payload: dict) -> str:
    data = payload.copy()

    data["exp"] = datetime.now(timezone.utc) + timedelta(
        hours=Config.JWT_EXPIRES_HOURS
    )

    return jwt.encode(
        data,
        Config.JWT_SECRET,
        algorithm="HS256"
    )


def _get_token_from_header():
    header = request.headers.get("Authorization", "")

    if header.startswith("Bearer "):
        return header[7:]

    return None


def get_current_user():
    """
    Mengambil data user dari token JWT.
    Dipakai kalau suatu route perlu membaca user login saat ini.
    """
    token = _get_token_from_header()

    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            Config.JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_token_from_header()

        if not token:
            response = jsonify({
                "message": "Sesi tidak ditemukan. Silakan login kembali."
            })
            return no_cache_response(response), 401

        try:
            payload = jwt.decode(
                token,
                Config.JWT_SECRET,
                algorithms=["HS256"]
            )

        except jwt.ExpiredSignatureError:
            response = jsonify({
                "message": "Sesi berakhir. Silakan login kembali."
            })
            return no_cache_response(response), 401

        except jwt.InvalidTokenError:
            response = jsonify({
                "message": "Sesi tidak valid. Silakan login kembali."
            })
            return no_cache_response(response), 401

        g.user = payload
        return fn(*args, **kwargs)

    return wrapper


def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "user", None)

            if not user:
                response = jsonify({
                    "message": "Sesi tidak ditemukan. Silakan login kembali."
                })
                return no_cache_response(response), 401

            if user.get("role") not in roles:
                response = jsonify({
                    "message": "Anda tidak memiliki akses untuk aksi ini."
                })
                return no_cache_response(response), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator