// Global State untuk menampung item di keranjang belanja
let cart = [];
let discountPercent = 10; // Diskon default sesuai mockup (10%)
let selectedMethod = "CASH";

// ==========================================
// 1. LOGIKA INTERAKSI HALAMAN LOGIN
// ==========================================
const btnLogin = document.getElementById('btn-login-submit');
if (btnLogin) {
    btnLogin.addEventListener('click', () => {
        const user = document.getElementById('username').value;
        const pass = document.getElementById('password').value;

        // Hitung API login backend
        fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user, password: pass })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') { 
                window.location.href = data.redirect; 
            } else { 
                alert(data.message); 
            }
        })
        .catch(err => console.error("Error Login:", err));
    });
}

// ==========================================
// 2. LOGIKA KERANJANG & BILLING KASIR
// ==========================================
const gridProduk = document.querySelector('.grid-produk');
const cartContainer = document.getElementById('cart-items');
const subtotalEl = document.getElementById('subtotal-val');
const diskonEl = document.getElementById('diskon-val');
const totalEl = document.getElementById('total-val');
const cashInput = document.getElementById('cash-input');
const changeEl = document.getElementById('change-val');

// Deteksi Klik pada Card Produk
if (gridProduk) {
    gridProduk.addEventListener('click', (e) => {
        const card = e.target.closest('.card-produk');
        
        // Abaikan jika bukan card produk atau jika produk stok habis
        if (!card || card.classList.contains('stok-habis')) return;

        const id = card.dataset.id;
        const nama = card.dataset.nama;
        const harga = parseInt(card.dataset.harga);

        // Cek apakah produk sudah ada di keranjang
        const existingItem = cart.find(item => item.id === id);
        if (existingItem) { 
            existingItem.qty += 1; 
        } else { 
            cart.push({ id, nama, harga, qty: 1 }); 
        }
        
        updateCartUI();
    });
}

// Fungsi Update Tampilan Keranjang & Total Harga
function updateCartUI() {
    if (cart.length === 0) {
        cartContainer.innerHTML = '<p class="empty-text">Belum ada menu yang dipilih</p>';
        subtotalEl.innerText = "Rp 0"; 
        diskonEl.innerText = "- Rp 0"; 
        totalEl.innerText = "Rp 0"; 
        changeEl.innerText = "Rp 0";
        if (cashInput) cashInput.value = '';
        return;
    }

    cartContainer.innerHTML = "";
    let subtotal = 0;

    // Loop data keranjang ke elemen HTML
    cart.forEach(item => {
        const itemSubtotal = item.harga * item.qty;
        subtotal += itemSubtotal;

        const div = document.createElement('div');
        div.className = 'item-cart';
        div.innerHTML = `
            <div>
                <span style="font-size:10px; color:#D36A00; font-weight:bold;">${item.id}</span>
                <h4 style="font-size:13px; margin:2px 0;">${item.nama}</h4>
                <div class="qty-control">
                    <button class="qty-btn" onclick="changeQty('${item.id}', -1)">-</button>
                    <span style="font-size:13px; font-weight:bold;">${item.qty}</span>
                    <button class="qty-btn" onclick="changeQty('${item.id}', 1)">+</button>
                </div>
            </div>
            <div style="font-weight:bold; font-size:13px; color:#6F3800;">Rp ${itemSubtotal.toLocaleString('id-ID')}</div>
        `;
        cartContainer.appendChild(div);
    });

    // Hitung Ringkasan Pembayaran
    const diskon = subtotal * (discountPercent / 100);
    const total = subtotal - diskon;

    subtotalEl.innerText = `Rp ${subtotal.toLocaleString('id-ID')}`;
    diskonEl.innerText = `- Rp ${diskon.toLocaleString('id-ID')}`;
    totalEl.innerText = `Rp ${total.toLocaleString('id-ID')}`;
    
    calculateChange(total);
}

// Fungsi Tambah / Kurang Qty Item di Keranjang (Akses via Window Object)
window.changeQty = function(id, delta) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    
    item.qty += delta;
    
    // Jika qty 0, hapus dari keranjang
    if (item.qty <= 0) {
        cart = cart.filter(i => i.id !== id);
    }
    updateCartUI();
};

// ==========================================
// 3. LOGIKA KALKULATOR KEMBALIAN
// ==========================================
if (cashInput) {
    cashInput.addEventListener('input', () => {
        // Ambil angka total harga saja dari teks UI
        const total = parseInt(totalEl.innerText.replace(/[^\d]/g, '')) || 0;
        calculateChange(total);
    });
}

function calculateChange(totalHarga) {
    if (!cashInput) return;
    const cashPaid = parseInt(cashInput.value) || 0;
    const change = cashPaid - totalHarga;
    
    // Tampilkan kembalian jika uangnya cukup, jika tidak tampilkan Rp 0
    changeEl.innerText = change >= 0 ? `Rp ${change.toLocaleString('id-ID')}` : "Rp 0";
}

// ==========================================
// 4. PILIHAN METODE PEMBAYARAN
// ==========================================
document.querySelectorAll('.method-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.method-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        selectedMethod = this.dataset.method;
    });
});

// ==========================================
// 5. TOMBOL PROSES & RESET KASIR
// ==========================================
const btnProses = document.getElementById('btn-proses-bayar');
if (btnProses) {
    btnProses.addEventListener('click', () => {
        if (cart.length === 0) return alert("Keranjang belanja masih kosong!");
        
        const custName = document.getElementById('cust-name').value || "General Customer";
        const custTable = document.getElementById('cust-table').value || "TA";
        const totalHarga = parseInt(totalEl.innerText.replace(/[^\d]/g, '')) || 0;
        const cashPaid = parseInt(cashInput.value) || 0;

        if (selectedMethod === "CASH" && cashPaid < totalHarga) {
            return alert("Uang tunai yang dibayarkan masih kurang!");
        }

        // Kirim data transaksi dummy ke backend
        fetch('/api/transaksi', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                customer: custName,
                meja: custTable,
                items: cart,
                total: totalHarga,
                metode: selectedMethod
            })
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message); // Menampilkan pesan sukses dari Flask
            
            // Bersihkan form setelah sukses bayar
            cart = [];
            if(cashInput) cashInput.value = '';
            document.getElementById('cust-name').value = '';
            document.getElementById('cust-table').value = '';
            updateCartUI();
        })
        .catch(err => console.error("Error Transaksi:", err));
    });
}

// Tombol Reset Keranjang
const btnReset = document.getElementById('btn-reset-cart');
if (btnReset) {
    btnReset.addEventListener('click', () => { 
        cart = []; 
        if(cashInput) cashInput.value = ''; 
        document.getElementById('cust-name').value = '';
        document.getElementById('cust-table').value = '';
        updateCartUI(); 
    });
}