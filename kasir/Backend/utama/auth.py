from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, make_response
from werkzeug.security import check_password_hash
from dotenv import load_dotenv, find_dotenv
from pymysql.cursors import DictCursor
import pymysql
import os

utama_auth = Blueprint('utama_auth', __name__)

load_dotenv(find_dotenv())


# ======================================================
# KONEKSI DATABASE
# ======================================================
def get_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 4000)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=DictCursor,
        autocommit=True,
        ssl={"ssl": {}}
    )


def clean(value):
    return str(value or "").strip()


def password_valid(password_hash, password_input):
    """
    Mengecek password hash dari database.
    Password harus dibuat dengan werkzeug generate_password_hash().
    """
    try:
        return check_password_hash(password_hash or "", password_input or "")
    except Exception:
        return False


def no_cache_response(response):
    """
    Mencegah browser menyimpan halaman login di cache.
    Jadi setelah login, tombol back browser tidak menampilkan login lama.
    """
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ======================================================
# HALAMAN LOGIN
# ======================================================
@utama_auth.route('/login')
def login():
    if session.get('logged_in') and session.get('role') == 'kasir':
        response = make_response(redirect('/kasir'))
        return no_cache_response(response)

    response = make_response(render_template('index.html'))
    return no_cache_response(response)


# ======================================================
# API LOGIN KASIR
# ======================================================
@utama_auth.route('/api/login', methods=['POST'])
def api_login():
    if session.get('logged_in') and session.get('role') == 'kasir':
        response = jsonify({
            'status': 'success',
            'message': 'Anda sudah login.',
            'redirect': '/kasir'
        })
        return no_cache_response(response)

    data = request.get_json(silent=True) or request.form or {}

    username = clean(data.get('username'))
    password = clean(data.get('password'))

    if not username or not password:
        response = jsonify({
            'status': 'error',
            'message': 'Username dan password wajib diisi.'
        })
        return no_cache_response(response), 400

    conn = None

    try:
        conn = get_conn()

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    nama,
                    username,
                    email,
                    password_hash,
                    role,
                    status,
                    is_active
                FROM users
                WHERE role = 'kasir'
                  AND (
                        username = %s
                        OR email = %s
                      )
                LIMIT 1
            """, (username, username))

            user = cursor.fetchone()

        if not user:
            response = jsonify({
                'status': 'error',
                'message': 'Username atau password salah.'
            })
            return no_cache_response(response), 401

        status_user = clean(user.get('status') or 'Aktif').lower()

        try:
            is_active = int(user.get('is_active') if user.get('is_active') is not None else 1)
        except Exception:
            is_active = 0

        if status_user != 'aktif' or is_active != 1:
            response = jsonify({
                'status': 'error',
                'message': 'Akun kasir sedang nonaktif. Hubungi admin.'
            })
            return no_cache_response(response), 403

        if not password_valid(user.get('password_hash'), password):
            response = jsonify({
                'status': 'error',
                'message': 'Username atau password salah.'
            })
            return no_cache_response(response), 401

        nama_kasir = (
            user.get('nama')
            or user.get('username')
            or 'kasir'
        )

        session.clear()
        session['logged_in'] = True
        session['user_id'] = user.get('id')
        session['kasir_id'] = user.get('id')
        session['username'] = user.get('username')
        session['kasir_username'] = user.get('username')
        session['nama'] = nama_kasir
        session['kasir_nama'] = nama_kasir
        session['role'] = 'kasir'
        session.modified = True

        response = jsonify({
            'status': 'success',
            'message': 'Login berhasil.',
            'redirect': '/kasir'
        })

        return no_cache_response(response)

    except Exception as err:
        print(f"[LOGIN KASIR ERROR] {err}")

        response = jsonify({
            'status': 'error',
            'message': 'Terjadi kesalahan saat login. Coba lagi nanti.'
        })

        return no_cache_response(response), 500

    finally:
        if conn:
            conn.close()


# ======================================================
# LOGOUT
# ======================================================
@utama_auth.route('/logout')
def logout():
    session.clear()

    response = make_response(redirect(url_for('utama_auth.login')))
    return no_cache_response(response)