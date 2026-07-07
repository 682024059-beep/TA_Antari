"""
Helper membuat baris notifikasi (lonceng) di database.
Dipanggil dari route produk, transaksi, diskon.
"""
from db_conn import query


def create_notifikasi(target_role="admin", tipe="sistem", judul="", pesan="", ref_kode=None):
    query(
        "INSERT INTO notifikasi (target_role, tipe, judul, pesan, ref_kode) VALUES (%s,%s,%s,%s,%s)",
        (target_role, tipe, judul, pesan, ref_kode),
        fetch=None,
    )
