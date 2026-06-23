"""
app.py
Entry point aplikasi Antari Admin.

Cara jalankan (lihat juga README.md):
    pip install -r requirements.txt
    python app.py

Aplikasi akan otomatis membuat database SQLite (antari.db) berisi data contoh
saat pertama kali dijalankan, lalu bisa diakses di http://127.0.0.1:5000
"""

from pathlib import Path

from flask import Flask

from database import DB_PATH
import seed as seed_module

from routes.pages import bp as pages_bp
from routes.api_produk import bp as api_produk_bp
from routes.api_diskon import bp as api_diskon_bp
from routes.api_penjualan import bp as api_penjualan_bp

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


def create_app():
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
        static_url_path="/static",
    )

    # Database: dibuat otomatis kalau file antari.db belum ada,
    # sekaligus diisi data contoh (produk, diskon, transaksi).
    if not DB_PATH.exists():
        seed_module.seed()

    app.register_blueprint(pages_bp)
    app.register_blueprint(api_produk_bp)
    app.register_blueprint(api_diskon_bp)
    app.register_blueprint(api_penjualan_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
