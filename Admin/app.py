import datetime
import os

from flask import Flask, jsonify, redirect, send_from_directory
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from config import Config
from db_conn import close_db, test_connection
from Backend.Admin.auth import bp as auth_bp
from Backend.Admin.diskon import bp as diskon_bp
from Backend.Admin.laporan import bp as laporan_bp
from Backend.Admin.notifikasi import bp as notifikasi_bp
from Backend.Admin.produk import bp as produk_bp
from Backend.Admin.profil import bp as profil_bp
from Backend.Admin.transaksi import bp as transaksi_bp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_ADMIN_DIR = os.path.join(BASE_DIR, "Frontend", "Admin")


class ISOJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(o, datetime.date):
            return o.strftime("%Y-%m-%d")
        if isinstance(o, datetime.timedelta):
            return str(o)
        return DefaultJSONProvider.default(o)


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)
    app.json_provider_class = ISOJSONProvider
    app.json = ISOJSONProvider(app)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    origins = Config.CORS_ORIGIN
    origins = "*" if origins.strip() == "*" else [o.strip() for o in origins.split(",")]
    CORS(app, origins=origins, supports_credentials=True)

    app.teardown_appcontext(close_db)

    app.register_blueprint(auth_bp)
    app.register_blueprint(profil_bp)
    app.register_blueprint(produk_bp)
    app.register_blueprint(diskon_bp)
    app.register_blueprint(transaksi_bp)
    app.register_blueprint(laporan_bp)
    app.register_blueprint(notifikasi_bp)

    @app.get("/")
    def root():
        return redirect("/admin/login.html")

    @app.get("/admin")
    @app.get("/admin/")
    def admin_root():
        return redirect("/admin/dashboard.html")

    @app.get("/admin/<path:filename>")
    def admin_static(filename):
        return send_from_directory(FRONTEND_ADMIN_DIR, filename)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "app": "antari-admin"})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"message": "Endpoint atau halaman tidak ditemukan."}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"message": "Ukuran file terlalu besar (maks 5MB)."}), 413

    @app.errorhandler(Exception)
    def handle_error(e):
        code = getattr(e, "code", 500)
        if isinstance(code, int) and 400 <= code < 600:
            return jsonify({"message": str(e)}), code
        app.logger.exception(e)
        return jsonify({"message": "Terjadi kesalahan server."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    test_connection()
    print(f"[ANTARI Admin] Server berjalan di http://localhost:{Config.PORT}")
    app.run(host="0.0.0.0", port=Config.PORT, debug=(Config.FLASK_ENV != "production"))
