"""
routes/pages.py
Route untuk merender halaman (HTML shell). Data tabel/statistik yang dinamis
diambil belakangan oleh JavaScript lewat endpoint /api/... (lihat api_*.py).
Pemisahan ini membuat frontend & backend terstruktur rapi: backend hanya
mengirim data JSON, sedangkan tampilan & interaksi sepenuhnya diatur oleh
HTML/CSS/JS di folder frontend/.
"""

from flask import Blueprint, render_template

bp = Blueprint("pages", __name__)


@bp.get("/")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")


@bp.get("/produk")
def manage_produk():
    return render_template("manage_produk.html", active_page="produk")


@bp.get("/produk/tambah")
def tambah_produk():
    return render_template("tambah_produk.html", active_page="produk")


@bp.get("/diskon")
def diskon():
    return render_template("diskon.html", active_page="diskon")


@bp.get("/penjualan")
def riwayat_penjualan():
    return render_template("riwayat_penjualan.html", active_page="penjualan")


@bp.get("/settings")
def settings():
    return render_template("placeholder.html", active_page="settings", judul="Settings")


@bp.get("/support")
def support():
    return render_template("placeholder.html", active_page="support", judul="Support")


@bp.get("/logout")
def logout():
    return render_template("placeholder.html", active_page="logout", judul="Anda telah logout")
