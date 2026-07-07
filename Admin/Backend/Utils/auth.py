"""
Autentikasi JWT untuk Flask.
Token dikirim frontend lewat header: Authorization: Bearer <token>
"""
import jwt
from functools import wraps
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, g
from config import Config


def generate_token(payload: dict) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRES_HOURS)
    return jwt.encode(data, Config.JWT_SECRET, algorithm="HS256")


def _get_token_from_header():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _get_token_from_header()
        if not token:
            return jsonify({"message": "Sesi tidak ditemukan. Silakan login kembali."}), 401
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Sesi berakhir. Silakan login kembali."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Sesi tidak valid. Silakan login kembali."}), 401
        g.user = payload  # {id, username, nama, role}
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, "user", None)
            if not user or user.get("role") not in roles:
                return jsonify({"message": "Anda tidak memiliki akses untuk aksi ini."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
