import os
from flask import Flask, redirect, url_for, request
from dotenv import load_dotenv, find_dotenv

from Backend.utama.auth import utama_auth
from Backend.utama.kasir import utama_kasir


load_dotenv(find_dotenv())

app = Flask(
    __name__,
    static_folder='Frontend/utama',
    template_folder='Frontend/utama'
)

app.secret_key = os.getenv("SECRET_KEY", "antari-coffee-secret-key")

@app.after_request
def add_no_cache_headers(response):
    if request.path.startswith("/kasir") or request.path.startswith("/riwayat") or request.path.startswith("/api"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.route('/')
def index():
    return redirect(url_for('utama_auth.login'))


app.register_blueprint(utama_auth)
app.register_blueprint(utama_kasir)


if __name__ == '__main__':
    app.run(debug=True)