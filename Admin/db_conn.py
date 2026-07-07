import ssl as ssl_lib

import pymysql
import pymysql.cursors
from flask import g

from config import Config


def _connect():
    ssl_ctx = ssl_lib.create_default_context() if Config.DB_SSL else None
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        ssl=ssl_ctx,
    )


def get_db():
    if "db_conn" not in g:
        g.db_conn = _connect()
    else:
        try:
            g.db_conn.ping(reconnect=True)
        except Exception:
            g.db_conn = _connect()
    return g.db_conn


def close_db(e=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()


def test_connection():
    try:
        conn = _connect()
        conn.ping()
        conn.close()
        print("[TiDB/MySQL] Koneksi database berhasil.")
        return True
    except Exception as err:
        print(f"[TiDB/MySQL] Gagal konek ke database: {err}")
        return False


def query(sql, params=None, fetch="all"):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        if fetch == "all":
            return cur.fetchall()
        if fetch == "one":
            return cur.fetchone()
        return cur.lastrowid
