from flask import Blueprint, request, jsonify
from model import query_fetchall, query_fetchone, query_execute
from functools import wraps
import jwt
import os
from werkzeug.utils import secure_filename
from config import config

produk_bp = Blueprint('produk', __name__)


# Reuse decorator dari dashboard - harusnya dibuat jadi middleware terpisah
# tapi buat sekarang duplikat dulu biar ga ribet import
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Login dulu ya'}), 401
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            request.admin = payload
        except:
            return jsonify({'success': False, 'message': 'Token tidak valid'}), 401
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    """Cek apakah ekstensi file diizinkan"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


@produk_bp.route('/', methods=['GET'])
@login_required
def get_all_produk():
    """
    Ambil semua produk dengan filter dan pagination
    Query params: page, limit, kategori, search
    """
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 3))  # 3 per halaman sesuai desain
    kategori_id = request.args.get('kategori', None)
    search = request.args.get('search', '').strip()
    
    offset = (page - 1) * limit
    
    # Bangun query dinamis berdasarkan filter
    where_clauses = []
    params = []
    
    if kategori_id:
        where_clauses.append("p.kategori_id = %s")
        params.append(kategori_id)
    
    if search:
        where_clauses.append("(p.nama_produk LIKE %s OR p.kode_produk LIKE %s)")
        params.extend([f'%{search}%', f'%{search}%'])
    
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    # Hitung total data dulu (buat pagination)
    count_sql = f"""
        SELECT COUNT(*) as total 
        FROM produk p 
        LEFT JOIN kategori k ON p.kategori_id = k.id
        {where_sql}
    """
    total_data = query_fetchone(count_sql, params)
    total = total_data['total'] if total_data else 0
    
    # Ambil data dengan pagination
    data_sql = f"""
        SELECT 
            p.id, p.kode_produk, p.nama_produk, 
            k.nama_kategori as kategori,
            p.harga, p.stok, p.foto, p.status,
            p.created_at
        FROM produk p
        LEFT JOIN kategori k ON p.kategori_id = k.id
        {where_sql}
        ORDER BY p.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])
    produk_list = query_fetchall(data_sql, params)
    
    # Format harga biar lebih enak dibaca
    for p in produk_list:
        p['harga_format'] = f"Rp {int(p['harga']):,}".replace(',', '.')
    
    return jsonify({
        'success': True,
        'data': produk_list,
        'pagination': {
            'total': total,
            'page': page,
            'limit': limit,
            'total_halaman': (total + limit - 1) // limit
        }
    }), 200


@produk_bp.route('/kategori', methods=['GET'])
@login_required
def get_kategori():
    """Ambil semua kategori buat dropdown filter"""
    kategori = query_fetchall("SELECT * FROM kategori ORDER BY nama_kategori")
    return jsonify({'success': True, 'data': kategori}), 200


@produk_bp.route('/<int:id>', methods=['GET'])
@login_required
def get_produk_by_id(id):
    """Ambil detail satu produk berdasarkan ID"""
    produk = query_fetchone("""
        SELECT p.*, k.nama_kategori as kategori
        FROM produk p
        LEFT JOIN kategori k ON p.kategori_id = k.id
        WHERE p.id = %s
    """, (id,))
    
    if not produk:
        return jsonify({'success': False, 'message': 'Produk tidak ditemukan'}), 404
    
    return jsonify({'success': True, 'data': produk}), 200


@produk_bp.route('/', methods=['POST'])
@login_required
def tambah_produk():
    """
    Tambah produk baru
    Form data: kode_produk, nama_produk, kategori_id, harga, stok, foto (file)
    """
    # Ambil data dari form (bukan JSON karena ada upload file)
    kode = request.form.get('kode_produk', '').strip()
    nama = request.form.get('nama_produk', '').strip()
    kategori_id = request.form.get('kategori_id')
    harga = request.form.get('harga')
    stok = request.form.get('stok', 0)
    
    # Validasi field wajib
    if not kode or not nama or not kategori_id or not harga:
        return jsonify({'success': False, 'message': 'Semua field wajib diisi'}), 400
    
    # Cek kode produk udah ada belum
    existing = query_fetchone("SELECT id FROM produk WHERE kode_produk = %s", (kode,))
    if existing:
        return jsonify({'success': False, 'message': f'Kode produk {kode} sudah digunakan'}), 400
    
    # Handle upload foto
    foto_filename = None
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename != '' and allowed_file(foto.filename):
            foto_filename = secure_filename(f"{kode}_{foto.filename}")
            foto.save(os.path.join(config.UPLOAD_FOLDER, foto_filename))
    
    # Tentukan status berdasarkan stok
    status = 'habis' if int(stok) == 0 else 'tersedia'
    
    result = query_execute("""
        INSERT INTO produk (kode_produk, nama_produk, kategori_id, harga, stok, foto, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (kode, nama, kategori_id, harga, stok, foto_filename, status))
    
    if result:
        return jsonify({'success': True, 'message': 'Produk berhasil ditambahkan', 'id': result}), 201
    else:
        return jsonify({'success': False, 'message': 'Gagal menambahkan produk'}), 500


@produk_bp.route('/<int:id>', methods=['PUT'])
@login_required
def update_produk(id):
    """Update data produk yang sudah ada"""
    
    # Cek produk ada dulu
    existing = query_fetchone("SELECT * FROM produk WHERE id = %s", (id,))
    if not existing:
        return jsonify({'success': False, 'message': 'Produk tidak ditemukan'}), 404
    
    nama = request.form.get('nama_produk', existing['nama_produk']).strip()
    kategori_id = request.form.get('kategori_id', existing['kategori_id'])
    harga = request.form.get('harga', existing['harga'])
    stok = request.form.get('stok', existing['stok'])
    
    # Handle foto baru kalau ada
    foto_filename = existing['foto']
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename != '' and allowed_file(foto.filename):
            # Hapus foto lama kalau ada
            if existing['foto']:
                old_path = os.path.join(config.UPLOAD_FOLDER, existing['foto'])
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            foto_filename = secure_filename(f"{existing['kode_produk']}_{foto.filename}")
            foto.save(os.path.join(config.UPLOAD_FOLDER, foto_filename))
    
    status = 'habis' if int(stok) == 0 else 'tersedia'
    
    query_execute("""
        UPDATE produk 
        SET nama_produk=%s, kategori_id=%s, harga=%s, stok=%s, foto=%s, status=%s
        WHERE id=%s
    """, (nama, kategori_id, harga, stok, foto_filename, status, id))
    
    return jsonify({'success': True, 'message': 'Produk berhasil diupdate'}), 200


@produk_bp.route('/<int:id>', methods=['DELETE'])
@login_required
def hapus_produk(id):
    """Hapus produk berdasarkan ID"""
    
    existing = query_fetchone("SELECT * FROM produk WHERE id = %s", (id,))
    if not existing:
        return jsonify({'success': False, 'message': 'Produk tidak ditemukan'}), 404
    
    # Hapus foto dari storage juga
    if existing['foto']:
        foto_path = os.path.join(config.UPLOAD_FOLDER, existing['foto'])
        if os.path.exists(foto_path):
            os.remove(foto_path)
    
    query_execute("DELETE FROM produk WHERE id = %s", (id,))
    
    return jsonify({'success': True, 'message': 'Produk berhasil dihapus'}), 200