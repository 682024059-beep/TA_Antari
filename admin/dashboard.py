from flask import Blueprint, request, jsonify
from model import query_fetchall, query_fetchone
from functools import wraps
import jwt
from config import config

dashboard_bp = Blueprint('dashboard', __name__)


# ---- Middleware / Decorator buat cek token ----
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Akses ditolak, login dulu'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            request.admin = payload  # simpen info admin di request
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token expired, silakan login ulang'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token tidak valid'}), 401
        
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Ambil statistik untuk kartu-kartu di dashboard"""
    
    total_produk = query_fetchone("SELECT COUNT(*) as total FROM produk")
    total_transaksi = query_fetchone("SELECT COUNT(*) as total FROM transaksi")
    total_pendapatan = query_fetchone("SELECT SUM(total) as total FROM transaksi WHERE status != 'cancelled'")
    stok_habis = query_fetchone("SELECT COUNT(*) as total FROM produk WHERE status = 'habis'")
    
    return jsonify({
        'success': True,
        'data': {
            'total_produk': total_produk['total'] if total_produk else 0,
            'total_transaksi': total_transaksi['total'] if total_transaksi else 0,
            'total_pendapatan': float(total_pendapatan['total']) if total_pendapatan and total_pendapatan['total'] else 0,
            'stok_habis': stok_habis['total'] if stok_habis else 0,
            # Persentase perubahan - ini harusnya diitung dari data historis
            # Sementara hardcode dulu buat demo
            'persen_produk': '+12%',
            'persen_transaksi': '+5.4%',
            'persen_pendapatan': '+8.1%'
        }
    }), 200


@dashboard_bp.route('/transaksi-terkini', methods=['GET'])
@login_required
def get_transaksi_terkini():
    """Ambil transaksi terbaru buat ditampilin di dashboard"""
    
    transaksi = query_fetchall("""
        SELECT t.order_id, t.nama_customer, t.total, t.status, t.created_at,
               GROUP_CONCAT(p.nama_produk SEPARATOR ', ') as menu
        FROM transaksi t
        LEFT JOIN detail_transaksi dt ON t.id = dt.transaksi_id
        LEFT JOIN produk p ON dt.produk_id = p.id
        GROUP BY t.id
        ORDER BY t.created_at DESC
        LIMIT 5
    """)
    
    return jsonify({
        'success': True,
        'data': transaksi
    }), 200


@dashboard_bp.route('/stok-hampir-habis', methods=['GET'])
@login_required
def get_stok_hampir_habis():
    """Ambil produk yang stoknya mau habis (stok < 5)"""
    
    # Di sini pake dummy data dulu karena tabel inventaris belum ada
    # Nanti bisa disambungin ke tabel beneran
    data = [
        {'nama': 'Arabica Beans', 'kode': 'AB-001', 'stok': 2, 'satuan': 'kg', 'min_stok': 5},
        {'nama': 'Barista Oat Milk', 'kode': 'BM-042', 'stok': 12, 'satuan': 'pcs', 'min_stok': 24},
        {'nama': 'Salted Caramel', 'kode': 'SC-009', 'stok': 3, 'satuan': 'btl', 'min_stok': 10},
        {'nama': 'Paper Cup L', 'kode': 'PC-121', 'stok': 50, 'satuan': 'pcs', 'min_stok': 200},
    ]
    
    return jsonify({'success': True, 'data': data}), 200


@dashboard_bp.route('/weekly-sales', methods=['GET'])
@login_required
def get_weekly_sales():
    """Data penjualan per hari dalam seminggu"""
    
    # Query ini nanti bisa disesuaikan dengan kebutuhan
    data = query_fetchall("""
        SELECT 
            DAYNAME(created_at) as hari,
            DAYOFWEEK(created_at) as urutan,
            SUM(total) as total_penjualan,
            COUNT(*) as jumlah_order
        FROM transaksi
        WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            AND status != 'cancelled'
        GROUP BY DAYNAME(created_at), DAYOFWEEK(created_at)
        ORDER BY urutan
    """)
    
    # Kalo data kosong, kasih dummy data biar grafik ga kosong
    if not data:
        data = [
            {'hari': 'Mon', 'total_penjualan': 850000, 'jumlah_order': 12},
            {'hari': 'Tue', 'total_penjualan': 1200000, 'jumlah_order': 18},
            {'hari': 'Wed', 'total_penjualan': 980000, 'jumlah_order': 14},
            {'hari': 'Thu', 'total_penjualan': 1500000, 'jumlah_order': 22},
            {'hari': 'Fri', 'total_penjualan': 1800000, 'jumlah_order': 28},
            {'hari': 'Sat', 'total_penjualan': 2100000, 'jumlah_order': 35},
            {'hari': 'Sun', 'total_penjualan': 1650000, 'jumlah_order': 25},
        ]
    
    return jsonify({'success': True, 'data': data}), 200