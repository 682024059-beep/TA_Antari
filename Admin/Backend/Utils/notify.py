"""
Helper membuat baris notifikasi (lonceng) di database.

Dipakai untuk:
1. Notifikasi admin
2. Notifikasi kasir saat produk ditambah, diupdate, dihapus
3. Notifikasi kasir saat stok menipis atau habis
"""

from db_conn import query


BATAS_STOK_MENIPIS = 5


def create_notifikasi(
    target_role="admin",
    tipe="sistem",
    judul="",
    pesan="",
    ref_kode=None
):
    """
    Membuat data notifikasi ke tabel notifikasi.
    target_role: admin / kasir / all
    """

    target_role = (target_role or "admin").strip()
    tipe = (tipe or "sistem").strip()
    judul = (judul or "Notifikasi").strip()
    pesan = (pesan or "").strip()

    try:
        query(
            """
            INSERT INTO notifikasi
            (target_role, tipe, judul, pesan, ref_kode)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (target_role, tipe, judul, pesan, ref_kode),
            fetch=None,
        )

        print(f"[Notifikasi] {target_role} | {tipe} | {judul}")

    except Exception as err:
        print(f"[Notifikasi] Gagal membuat notifikasi: {err}")


def notif_produk_kasir(tipe, kode, nama):
    """
    Notifikasi untuk kasir saat admin mengubah data produk.

    tipe:
    - produk_baru
    - produk_update
    - produk_hapus
    """

    kode = str(kode or "").strip()
    nama = str(nama or "").strip()

    if not kode or not nama:
        return

    if tipe == "produk_baru":
        judul = "Produk Baru"
        pesan = f'Produk "{nama}" ({kode}) baru ditambahkan oleh admin.'

    elif tipe == "produk_update":
        judul = "Produk Diperbarui"
        pesan = f'Produk "{nama}" ({kode}) telah diperbarui oleh admin.'

    elif tipe == "produk_hapus":
        judul = "Produk Dihapus"
        pesan = f'Produk "{nama}" ({kode}) telah dihapus dari menu oleh admin.'

    else:
        tipe = "produk_update"
        judul = "Perubahan Produk"
        pesan = f'Produk "{nama}" ({kode}) mengalami perubahan.'

    create_notifikasi(
        target_role="kasir",
        tipe=tipe,
        judul=judul,
        pesan=pesan,
        ref_kode=kode,
    )


def notif_stok_berubah(kode, nama, stok_lama, stok_baru):
    """
    Notifikasi untuk kasir saat stok berubah dari aman menjadi menipis/habis.
    Supaya tidak spam, notifikasi hanya dibuat saat melewati batas.
    """

    kode = str(kode or "").strip()
    nama = str(nama or "").strip()

    if not kode or not nama:
        return

    try:
        stok_lama = int(stok_lama or 0)
        stok_baru = int(stok_baru or 0)
    except Exception:
        return

    if stok_baru <= 0 and stok_lama > 0:
        create_notifikasi(
            target_role="kasir",
            tipe="stok_habis",
            judul="Stok Produk Habis",
            pesan=f'Stok produk "{nama}" ({kode}) sudah habis.',
            ref_kode=kode,
        )

    elif stok_baru <= BATAS_STOK_MENIPIS and stok_lama > BATAS_STOK_MENIPIS:
        create_notifikasi(
            target_role="kasir",
            tipe="stok_menipis",
            judul="Stok Produk Menipis",
            pesan=f'Stok produk "{nama}" ({kode}) tinggal {stok_baru}.',
            ref_kode=kode,
        )


def notif_stok_langsung(kode, nama, stok):
    """
    Notifikasi untuk kasir saat produk baru langsung ditambahkan
    dalam kondisi stok menipis atau habis.
    """

    kode = str(kode or "").strip()
    nama = str(nama or "").strip()

    if not kode or not nama:
        return

    try:
        stok = int(stok or 0)
    except Exception:
        return

    if stok <= 0:
        create_notifikasi(
            target_role="kasir",
            tipe="stok_habis",
            judul="Stok Produk Habis",
            pesan=f'Stok produk "{nama}" ({kode}) sedang habis.',
            ref_kode=kode,
        )

    elif stok <= BATAS_STOK_MENIPIS:
        create_notifikasi(
            target_role="kasir",
            tipe="stok_menipis",
            judul="Stok Produk Menipis",
            pesan=f'Stok produk "{nama}" ({kode}) tinggal {stok}.',
            ref_kode=kode,
        )