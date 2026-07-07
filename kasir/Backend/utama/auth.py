from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

utama_auth = Blueprint('utama_auth', __name__)


@utama_auth.route('/login')
def login():
    return render_template('index.html')


@utama_auth.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if username == 'kasir' and password == 'antari123':
        session['logged_in'] = True
        session['username'] = username
        session['role'] = 'kasir'

        return jsonify({
            'status': 'success',
            'message': 'Login berhasil',
            'redirect': '/kasir'
        })

    return jsonify({
        'status': 'error',
        'message': 'Username atau password salah!'
    })


@utama_auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('utama_auth.login'))