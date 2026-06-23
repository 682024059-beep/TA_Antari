from flask import Blueprint, render_template, request, jsonify

utama_auth = Blueprint('utama_auth', __name__)

@utama_auth.route('/login')
def login():
    return render_template('index.html')

@utama_auth.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    # Username & password dummy untuk kasir masuk ke sistem
    if data.get('username') == 'kasir' and data.get('password') == 'antari123':
        return jsonify({"status": "success", "redirect": "/kasir"})
    return jsonify({"status": "error", "message": "Username atau password salah!"})