from flask import Flask, send_from_directory
from flask_cors import CORS
import os

# Import blueprint dari masing-masing modul
from backend.admin.login import login_bp
from backend.admin.dashboard import dashboard_bp
from backend.admin.manage_produk import produk_bp

from config import config

app = Flask(__name__, static_folder='frontend')
app.secret_key = config.SECRET_KEY
CORS(app)  # biar frontend bisa akses API-nya

# Daftarin semua blueprint
app.register_blueprint(login_bp, url_prefix='/api/auth')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
app.register_blueprint(produk_bp, url_prefix='/api/produk')


# Route buat serve file HTML frontend
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/admin/<path:filename>')
def serve_admin(filename):
    return send_from_directory('frontend/admin', filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('.', 'favicon.ico')


if __name__ == '__main__':
    # Bikin folder uploads kalo belum ada
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    
    print("=" * 40)
    print("  CoffeeShop Antari - Admin Panel")
    print("  Running at http://localhost:5000")
    print("=" * 40)
    
    app.run(debug=config.DEBUG, port=5000)