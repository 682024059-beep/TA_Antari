/**
 * manage-produk.js
 * Handle CRUD produk di halaman Manage Produk
 */

// Guard - cek login
if (!getToken()) {
    window.location.href = '/admin/login.html';
}

// State halaman
let currentPage = 1;
let totalHalaman = 1;
let currentEditId = null;
let currentHapusId = null;
let searchTimeout = null;

// Referensi elemen DOM
const produkBody = document.getElementById('produkBody');
const totalBadge = document.getElementById('totalBadge');
const paginationInfo = document.getElementById('paginationInfo');
const paginationBtns = document.getElementById('paginationBtns');
const searchInput = document.getElementById('searchInput');
const kategoriFilter = document.getElementById('kategoriFilter');
const modalOverlay = document.getElementById('modalOverlay');
const modalHapusOverlay = document.getElementById('modalHapusOverlay');
const modalTitle = document.getElementById('modalTitle');
const btnSimpan = document.getElementById('btnSimpan');
const toast = document.getElementById('toast');

// ---- Fungsi Utilitas ----

function tampilkanToast(pesan, tipe = 'sukses') {
    toast.textContent = pesan;
    toast.className = `toast ${tipe} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function bukaModal() {
    modalOverlay.classList.add('show');
}

function tutupModal() {
    modalOverlay.classList.remove('show');
    resetForm();
}

function bukaModalHapus(id, nama) {
    currentHapusId = id;
    document.getElementById('hapusNama').textContent = nama;
    modalHapusOverlay.classList.add('show');
}

function tutupModalHapus() {
    modalHapusOverlay.classList.remove('show');
    currentHapusId = null;
}

function resetForm() {
    document.getElementById('inputKode').value = '';
    document.getElementById('inputNama').value = '';
    document.getElementById('inputKategori').value = '';
    document.getElementById('inputHarga').value = '';
    document.getElementById('inputStok').value = '0';
    document.getElementById('inputFoto').value = '';
    currentEditId = null;
    modalTitle.textContent = 'Tambah Produk';
    btnSimpan.textContent = 'Simpan Produk';
    document.getElementById('inputKode').disabled = false;
}

function getKategoriClass(kategori) {
    const k = kategori?.toLowerCase().replace(/[^a-z]/g, '');
    if (k === 'coffee') return 'coffee';
    if (k === 'noncoffee') return 'non-coffee';
    if (k === 'pastry') return 'pastry';
    return '';
}

function getFotoUrl(fotoFilename) {
    if (!fotoFilename) {
        return 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=60&h=60&fit=crop';
    }
    return `/admin/uploads/${fotoFilename}`;
}

// ---- Load Data ----

async function loadKategori() {
    const result = await api.get('/produk/kategori');
    if (!result || !result.data.success) return;

    const options = result.data.data.map(k =>
        `<option value="${k.id}">${k.nama_kategori}</option>`
    ).join('');

    // Isi dropdown filter
    kategoriFilter.innerHTML = '<option value="">Semua Kategori</option>' + options;

    // Isi dropdown di modal
    document.getElementById('inputKategori').innerHTML =
        '<option value="">Pilih kategori...</option>' + options;
}

async function loadProduk() {
    produkBody.innerHTML = `<tr><td colspan="8" class="loading-text">Memuat data...</td></tr>`;

    const search = searchInput.value.trim();
    const kategori = kategoriFilter.value;

    let endpoint = `/produk/?page=${currentPage}&limit=3`;
    if (search) endpoint += `&search=${encodeURIComponent(search)}`;
    if (kategori) endpoint += `&kategori=${kategori}`;

    const result = await api.get(endpoint);

    if (!result || !result.data.success) {
        produkBody.innerHTML = `<tr><td colspan="8" class="loading-text">Gagal memuat produk</td></tr>`;
        return;
    }

    const { data, pagination } = result.data;
    totalHalaman = pagination.total_halaman;

    // Update info total
    totalBadge.textContent = `Total: ${pagination.total} Produk`;
    paginationInfo.textContent = `Menampilkan ${(currentPage - 1) * 3 + 1}-${Math.min(currentPage * 3, pagination.total)} dari ${pagination.total} produk`;

    if (data.length === 0) {
        produkBody.innerHTML = `<tr><td colspan="8" class="loading-text">Tidak ada produk yang ditemukan</td></tr>`;
        renderPaginasi(0, 0);
        return;
    }

    produkBody.innerHTML = data.map(p => `
        <tr>
            <td>
                <img 
                    class="foto-produk"
                    src="${getFotoUrl(p.foto)}"
                    alt="${p.nama_produk}"
                    onerror="this.src='https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=60&h=60&fit=crop'"
                >
            </td>
            <td><span class="kode-badge">${p.kode_produk}</span></td>
            <td><strong>${p.nama_produk}</strong></td>
            <td>
                <span class="kategori-badge ${getKategoriClass(p.kategori)}">
                    ${p.kategori || '-'}
                </span>
            </td>
            <td>${p.harga_format || 'Rp ' + Number(p.harga).toLocaleString('id-ID')}</td>
            <td class="${p.stok <= 3 ? 'stok-rendah' : ''}">${p.stok}</td>
            <td>
                <span class="status-badge ${p.status}">
                    ${p.status === 'tersedia' ? 'Tersedia' : 'Habis'}
                </span>
            </td>
            <td>
                <div class="aksi-btns">
                    <button class="btn-edit" onclick="editProduk(${p.id})" title="Edit">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                    <button class="btn-hapus" onclick="konfirmasiHapus(${p.id}, '${p.nama_produk}')" title="Hapus">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6l-1 14H6L5 6M10 11v6M14 11v6"/>
                            <path d="M9 6V4h6v2"/>
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

    renderPaginasi(pagination.total, pagination.total_halaman);
}

function renderPaginasi(total, totalPage) {
    if (total === 0) {
        paginationBtns.innerHTML = '';
        return;
    }

    let html = `
        <button class="page-btn" onclick="gantiHalaman(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>‹</button>
    `;

    for (let i = 1; i <= totalPage; i++) {
        // Tampilkan halaman 1, terakhir, dan sekitar halaman aktif
        if (i === 1 || i === totalPage || Math.abs(i - currentPage) <= 1) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="gantiHalaman(${i})">${i}</button>`;
        } else if (Math.abs(i - currentPage) === 2) {
            html += `<span class="page-btn" style="cursor:default">...</span>`;
        }
    }

    html += `
        <button class="page-btn" onclick="gantiHalaman(${currentPage + 1})" ${currentPage === totalPage ? 'disabled' : ''}>›</button>
    `;

    paginationBtns.innerHTML = html;
}

function gantiHalaman(hal) {
    if (hal < 1 || hal > totalHalaman) return;
    currentPage = hal;
    loadProduk();
}

// ---- CRUD ----

// Klik tombol edit - isi form dengan data produk yang dipilih
async function editProduk(id) {
    const result = await api.get(`/produk/${id}`);
    if (!result || !result.data.success) {
        tampilkanToast('Gagal memuat data produk', 'error');
        return;
    }

    const p = result.data.data;
    currentEditId = id;

    document.getElementById('inputKode').value = p.kode_produk;
    document.getElementById('inputKode').disabled = true; // kode gak boleh diubah
    document.getElementById('inputNama').value = p.nama_produk;
    document.getElementById('inputKategori').value = p.kategori_id;
    document.getElementById('inputHarga').value = p.harga;
    document.getElementById('inputStok').value = p.stok;

    modalTitle.textContent = 'Edit Produk';
    btnSimpan.textContent = 'Update Produk';
    bukaModal();
}

function konfirmasiHapus(id, nama) {
    bukaModalHapus(id, nama);
}

// Simpan produk (tambah atau update)
async function simpanProduk() {
    const kode = document.getElementById('inputKode').value.trim();
    const nama = document.getElementById('inputNama').value.trim();
    const kategori = document.getElementById('inputKategori').value;
    const harga = document.getElementById('inputHarga').value;
    const stok = document.getElementById('inputStok').value;
    const fotoFile = document.getElementById('inputFoto').files[0];

    // Validasi sederhana
    if (!nama || !kategori || !harga) {
        tampilkanToast('Lengkapi semua field yang wajib diisi', 'error');
        return;
    }

    // Pakai FormData karena ada file upload
    const formData = new FormData();
    if (!currentEditId) formData.append('kode_produk', kode);
    formData.append('nama_produk', nama);
    formData.append('kategori_id', kategori);
    formData.append('harga', harga);
    formData.append('stok', stok);
    if (fotoFile) formData.append('foto', fotoFile);

    btnSimpan.disabled = true;
    btnSimpan.textContent = 'Menyimpan...';

    let result;
    if (currentEditId) {
        result = await api.putForm(`/produk/${currentEditId}`, formData);
    } else {
        result = await api.postForm('/produk/', formData);
    }

    btnSimpan.disabled = false;
    btnSimpan.textContent = currentEditId ? 'Update Produk' : 'Simpan Produk';

    if (result && result.data.success) {
        tampilkanToast(result.data.message, 'sukses');
        tutupModal();
        loadProduk();
    } else {
        tampilkanToast(result?.data?.message || 'Terjadi kesalahan', 'error');
    }
}

// Hapus produk setelah konfirmasi
async function hapusProduk() {
    if (!currentHapusId) return;

    const result = await api.delete(`/produk/${currentHapusId}`);

    if (result && result.data.success) {
        tampilkanToast('Produk berhasil dihapus', 'sukses');
        tutupModalHapus();

        // Kalo halaman ini jadi kosong, balik ke halaman sebelumnya
        if (currentPage > 1) currentPage--;
        loadProduk();
    } else {
        tampilkanToast(result?.data?.message || 'Gagal menghapus produk', 'error');
    }
}

// ---- Event Listeners ----

document.getElementById('btnTambah').addEventListener('click', () => {
    resetForm();
    bukaModal();
});

document.getElementById('modalClose').addEventListener('click', tutupModal);
document.getElementById('btnBatal').addEventListener('click', tutupModal);
document.getElementById('hapusClose').addEventListener('click', tutupModalHapus);
document.getElementById('hapusBatal').addEventListener('click', tutupModalHapus);
document.getElementById('btnSimpan').addEventListener('click', simpanProduk);
document.getElementById('hapusKonfirm').addEventListener('click', hapusProduk);

// Tutup modal kalo klik di luar area modal
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) tutupModal();
});

modalHapusOverlay.addEventListener('click', (e) => {
    if (e.target === modalHapusOverlay) tutupModalHapus();
});

// Search dengan debounce biar gak request terus setiap ketikan
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        loadProduk();
    }, 400);
});

// Filter kategori
kategoriFilter.addEventListener('change', () => {
    currentPage = 1;
    loadProduk();
});

// Logout
document.getElementById('btnLogout').addEventListener('click', () => {
    if (confirm('Yakin mau logout?')) {
        api.post('/auth/logout', {});
        removeToken();
        window.location.href = '/admin/login.html';
    }
});

// ---- Inisialisasi ----
async function init() {
    await loadKategori();
    await loadProduk();
}

init();