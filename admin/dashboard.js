/**
 * dashboard.js
 * Handle semua data dan interaksi di halaman dashboard
 */

// Proteksi halaman - kalau belum login redirect ke login
if (!getToken()) {
    window.location.href = '/admin/login.html';
}

// Tampilkan tanggal sekarang di topbar
function tampilkanTanggal() {
    const el = document.getElementById('tanggal-sekarang');
    const sekarang = new Date();
    const opsi = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const tgl = sekarang.toLocaleDateString('id-ID', opsi);
    const jam = sekarang.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
    el.textContent = `${tgl} · ${jam} WIB`;
}

tampilkanTanggal();

// Format angka jadi format rupiah
function formatRupiah(angka) {
    if (angka >= 1000000) {
        return `Rp ${(angka / 1000000).toFixed(1)}M`;
    } else if (angka >= 1000) {
        return `Rp ${(angka / 1000).toFixed(1)}K`;
    }
    return `Rp ${angka.toLocaleString('id-ID')}`;
}

// Ambil dan tampilkan statistik
async function loadStats() {
    const result = await api.get('/dashboard/stats');
    
    if (!result || !result.data.success) return;
    
    const d = result.data.data;
    
    document.getElementById('total-produk').textContent = d.total_produk.toLocaleString('id-ID');
    document.getElementById('total-transaksi').textContent = d.total_transaksi.toLocaleString('id-ID');
    document.getElementById('total-pendapatan').textContent = formatRupiah(d.total_pendapatan);
    document.getElementById('stok-habis').textContent = d.stok_habis;
    document.getElementById('persen-produk').textContent = d.persen_produk;
    document.getElementById('persen-transaksi').textContent = d.persen_transaksi;
    document.getElementById('persen-pendapatan').textContent = d.persen_pendapatan;
}

// Ambil dan render list stok hampir habis
async function loadStokHampirHabis() {
    const result = await api.get('/dashboard/stok-hampir-habis');
    const container = document.getElementById('stokList');
    
    if (!result || !result.data.success) {
        container.innerHTML = '<p class="loading-text">Gagal memuat data</p>';
        return;
    }
    
    const items = result.data.data;
    
    if (items.length === 0) {
        container.innerHTML = '<p class="loading-text">Semua stok aman!</p>';
        return;
    }
    
    // Gambar placeholder dari Unsplash sesuai nama item
    const fotoMap = {
        'Arabica Beans': 'https://images.unsplash.com/photo-1587734005433-7f7f61d5f3b4?w=60&h=60&fit=crop',
        'Barista Oat Milk': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=60&h=60&fit=crop',
        'Salted Caramel': 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=60&h=60&fit=crop',
        'Paper Cup L': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=60&h=60&fit=crop',
    };
    
    container.innerHTML = items.map(item => `
        <div class="stok-item">
            <img 
                class="stok-foto" 
                src="${fotoMap[item.nama] || 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=60&h=60&fit=crop'}"
                alt="${item.nama}"
                onerror="this.style.background='#F0E8E0'; this.src=''"
            >
            <div class="stok-info">
                <div class="stok-nama">${item.nama}</div>
                <div class="stok-kode">CODE: ${item.kode}</div>
            </div>
            <div class="stok-angka">
                <div class="stok-sisa">${item.stok} ${item.satuan}</div>
                <div class="stok-min">Min. ${item.min_stok} ${item.satuan}</div>
            </div>
        </div>
    `).join('');
}

// Ambil data grafik mingguan dan render dengan Chart.js
let chartInstance = null;

async function loadWeeklySales() {
    const result = await api.get('/dashboard/weekly-sales');
    
    if (!result || !result.data.success) return;
    
    const data = result.data.data;
    const labels = data.map(d => d.hari);
    const values = data.map(d => d.total_penjualan);
    
    const ctx = document.getElementById('salesChart').getContext('2d');
    
    if (chartInstance) chartInstance.destroy();
    
    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Penjualan (Rp)',
                data: values,
                backgroundColor: (context) => {
                    // Kasih warna beda di hari Sabtu (paling rame biasanya)
                    const index = context.dataIndex;
                    return labels[index] === 'Sat' ? '#C0392B' : '#F5D5D0';
                },
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => ` ${formatRupiah(context.parsed.y)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#8A8A8A', font: { size: 12 } }
                },
                y: {
                    grid: { color: '#F0F0F0' },
                    ticks: {
                        color: '#8A8A8A',
                        font: { size: 12 },
                        callback: (val) => formatRupiah(val)
                    }
                }
            }
        }
    });
}

// Ambil dan render tabel transaksi terkini
async function loadTransaksiTerkini() {
    const result = await api.get('/dashboard/transaksi-terkini');
    const tbody = document.getElementById('transaksiBody');
    
    if (!result || !result.data.success) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading-text">Gagal memuat transaksi</td></tr>';
        return;
    }
    
    const data = result.data.data;
    
    if (data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading-text">Belum ada transaksi</td></tr>';
        return;
    }
    
    const badgeClass = {
        'served': 'badge-served',
        'brewing': 'badge-brewing',
        'pending': 'badge-pending',
        'cancelled': 'badge-pending'
    };
    
    tbody.innerHTML = data.map(t => `
        <tr>
            <td>${t.order_id}</td>
            <td>${t.nama_customer}</td>
            <td>${t.menu || '-'}</td>
            <td><strong>Rp ${Number(t.total).toLocaleString('id-ID')}</strong></td>
            <td>
                <span class="badge ${badgeClass[t.status] || 'badge-pending'}">
                    ${t.status.toUpperCase()}
                </span>
            </td>
            <td>
                <button class="action-btn" title="Opsi">···</button>
            </td>
        </tr>
    `).join('');
}

// Handle logout
document.getElementById('btnLogout').addEventListener('click', () => {
    if (confirm('Yakin mau logout?')) {
        api.post('/auth/logout', {});
        removeToken();
        window.location.href = '/admin/login.html';
    }
});

// Inisialisasi semua data waktu halaman dimuat
async function init() {
    await Promise.all([
        loadStats(),
        loadStokHampirHabis(),
        loadWeeklySales(),
        loadTransaksiTerkini()
    ]);
}

init();