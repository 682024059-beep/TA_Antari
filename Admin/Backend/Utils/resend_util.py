"""
RESEND - dipakai untuk 3 keperluan email di ANTARI:

1. send_struk_email()        -> struk digital ke pelanggan setelah
   transaksi kasir selesai, jika kasir mengisi email pelanggan.
2. send_stok_menipis_email() -> alert ke email admin (RESEND_ADMIN_EMAIL)
   saat stok produk menyentuh batas menipis/habis.
3. send_password_changed_email() -> notifikasi keamanan ke email
   pemilik akun setiap kali password diganti (bukan menampilkan
   password, hanya pemberitahuan).

Semua fungsi "fail-soft": jika RESEND_API_KEY belum diisi atau
pengiriman gagal, error di-log tapi tidak menggagalkan proses utama.
"""
import resend
from config import Config

resend.api_key = Config.RESEND_API_KEY
FROM = Config.RESEND_FROM_EMAIL
ADMIN_EMAIL = Config.RESEND_ADMIN_EMAIL


def _rupiah(n):
    try:
        return "Rp" + f"{int(n):,}".replace(",", ".")
    except Exception:
        return "Rp0"


def _safe_send(payload, label):
    if not Config.RESEND_API_KEY:
        print(f'[Resend] Lewati kirim "{label}" — RESEND_API_KEY belum diset.')
        return {"ok": False, "skipped": True}
    try:
        result = resend.Emails.send(payload)
        return {"ok": True, "id": result.get("id")}
    except Exception as err:
        print(f'[Resend] Gagal kirim "{label}": {err}')
        return {"ok": False, "error": str(err)}


def send_struk_email(trx):
    email = trx.get("email_customer")
    if not email:
        return {"ok": False, "skipped": True, "reason": "no-email"}

    items_rows = "".join(
        f"""<tr>
            <td style="padding:6px 0;">{it['nama']} x{it['qty']}</td>
            <td style="padding:6px 0; text-align:right;">{_rupiah(it['subtotal'])}</td>
        </tr>"""
        for it in trx["items"]
    )

    html = f"""
    <div style="font-family:Arial,sans-serif; max-width:420px; margin:auto; color:#2b2118;">
      <h2 style="margin-bottom:0;">☕ ANTARI CoffeeShop</h2>
      <p style="color:#7a6a5c; margin-top:4px;">Struk Digital — Terima kasih atas kunjungan Anda!</p>
      <hr style="border:none; border-top:1px solid #e5ddd3;">
      <p style="font-size:13px; color:#7a6a5c;">
        No. Transaksi: <b>{trx['id']}</b><br>
        Tanggal: {trx['tanggal']} {trx['waktu']}<br>
        Kasir: {trx['kasir_username']}<br>
        Metode Bayar: {trx['metode']}
      </p>
      <table style="width:100%; border-collapse:collapse; font-size:14px;">{items_rows}</table>
      <hr style="border:none; border-top:1px solid #e5ddd3;">
      <table style="width:100%; font-size:14px;">
        <tr><td>Subtotal</td><td style="text-align:right;">{_rupiah(trx['subtotal'])}</td></tr>
        <tr><td>Diskon</td><td style="text-align:right;">-{_rupiah(trx['diskon_nominal'])}</td></tr>
        <tr style="font-weight:bold; font-size:16px;"><td>Total</td><td style="text-align:right;">{_rupiah(trx['total'])}</td></tr>
      </table>
      <p style="margin-top:24px; font-size:12px; color:#9c8c7d; text-align:center;">
        Struk ini dikirim otomatis oleh Sistem POS ANTARI. Simpan sebagai bukti pembayaran.
      </p>
    </div>"""

    return _safe_send(
        {"from": FROM, "to": email, "subject": f"Struk Digital ANTARI — {trx['id']}", "html": html},
        "struk digital",
    )


def send_stok_menipis_email(produk_list):
    if not ADMIN_EMAIL or not produk_list:
        return {"ok": False, "skipped": True}

    rows = "".join(
        f"""<tr>
            <td style="padding:4px 8px;">{p['kode']}</td>
            <td style="padding:4px 8px;">{p['nama']}</td>
            <td style="padding:4px 8px; text-align:center;">{p['stok']}</td>
        </tr>"""
        for p in produk_list
    )

    html = f"""
    <div style="font-family:Arial,sans-serif; max-width:480px; margin:auto; color:#2b2118;">
      <h2>⚠️ Peringatan Stok — ANTARI</h2>
      <p>Produk berikut butuh restock segera:</p>
      <table style="width:100%; border-collapse:collapse; font-size:13px; border:1px solid #e5ddd3;">
        <thead><tr style="background:#f6f1ea;">
          <th style="padding:4px 8px; text-align:left;">Kode</th>
          <th style="padding:4px 8px; text-align:left;">Nama Produk</th>
          <th style="padding:4px 8px;">Sisa Stok</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="margin-top:16px; font-size:12px; color:#9c8c7d;">Notifikasi otomatis dari Sistem POS ANTARI.</p>
    </div>"""

    return _safe_send(
        {"from": FROM, "to": ADMIN_EMAIL, "subject": "Peringatan: Stok Produk Menipis/Habis", "html": html},
        "alert stok menipis",
    )


def send_password_changed_email(to_email, nama):
    if not to_email:
        return {"ok": False, "skipped": True}
    html = f"""
    <div style="font-family:Arial,sans-serif; max-width:420px; margin:auto; color:#2b2118;">
      <h2>🔒 Password Diperbarui</h2>
      <p>Halo {nama or ''},</p>
      <p>Password akun ANTARI Anda baru saja diubah. Jika Anda tidak melakukan perubahan ini, segera hubungi admin sistem.</p>
      <p style="font-size:12px; color:#9c8c7d;">Email ini dikirim otomatis, mohon tidak membalas.</p>
    </div>"""
    return _safe_send(
        {"from": FROM, "to": to_email, "subject": "Password Akun ANTARI Diperbarui", "html": html},
        "notifikasi ganti password",
    )
