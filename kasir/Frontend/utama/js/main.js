// ======================================================
// ANTARI COFFEE - MAIN JAVASCRIPT
// ======================================================

// Global State Keranjang
let cart = [];
let discountPercent = 10;
let selectedMethod = "CASH";


// Format angka ke Rupiah
function formatRupiah(angka) {
    return `Rp ${Number(angka || 0).toLocaleString('id-ID')}`;
}


// ======================================================
// 1. LOGIN PAGE
// ======================================================

const loginForm = document.getElementById('loginForm');
const loginMessage = document.getElementById('loginMessage');
const togglePassword = document.getElementById('togglePassword');

if (loginForm) {
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();
        const btnLogin = document.getElementById('btn-login-submit');

        if (!username || !password) {
            if (loginMessage) {
                loginMessage.textContent = "Username dan password wajib diisi.";
                loginMessage.className = "login-message error";
            }
            return;
        }

        btnLogin.disabled = true;
        btnLogin.innerHTML = 'Memproses... <i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                if (loginMessage) {
                    loginMessage.textContent = data.message || "Login berhasil.";
                    loginMessage.className = "login-message success";
                }

                setTimeout(() => {
                    window.location.href = data.redirect || '/kasir';
                }, 400);

            } else {
                if (loginMessage) {
                    loginMessage.textContent = data.message || "Username atau password salah.";
                    loginMessage.className = "login-message error";
                } else {
                    alert(data.message || "Username atau password salah.");
                }
            }

        } catch (error) {
            console.error("Error Login:", error);

            if (loginMessage) {
                loginMessage.textContent = "Terjadi kesalahan koneksi ke server.";
                loginMessage.className = "login-message error";
            } else {
                alert("Terjadi kesalahan koneksi ke server.");
            }

        } finally {
            btnLogin.disabled = false;
            btnLogin.innerHTML = 'Masuk <i class="fa-solid fa-arrow-right"></i>';
        }
    });
}


// Toggle lihat password
if (togglePassword) {
    togglePassword.addEventListener('click', function() {
        const passwordInput = document.getElementById('password');

        if (!passwordInput) return;

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            this.classList.remove('fa-eye');
            this.classList.add('fa-eye-slash');
        } else {
            passwordInput.type = 'password';
            this.classList.remove('fa-eye-slash');
            this.classList.add('fa-eye');
        }
    });
}


// ======================================================
// 2. KERANJANG KASIR
// ======================================================

const gridProduk = document.querySelector('.grid-produk');
const cartContainer = document.getElementById('cart-items');
const subtotalEl = document.getElementById('subtotal-val');
const diskonEl = document.getElementById('diskon-val');
const totalEl = document.getElementById('total-val');
const cashInput = document.getElementById('cash-input');
const changeEl = document.getElementById('change-val');


// Klik produk untuk masuk keranjang
if (gridProduk) {
    gridProduk.addEventListener('click', function(e) {
        const card = e.target.closest('.card-produk');

        if (!card) return;

        if (card.classList.contains('stok-habis')) {
            alert("Produk ini sedang stok habis.");
            return;
        }

        const id = card.dataset.id;
        const nama = card.dataset.nama;
        const harga = parseInt(card.dataset.harga) || 0;

        const existingItem = cart.find(item => item.id === id);

        if (existingItem) {
            existingItem.qty += 1;
        } else {
            cart.push({
                id: id,
                nama: nama,
                harga: harga,
                qty: 1
            });
        }

        updateCartUI();
    });
}


// Update tampilan keranjang
function updateCartUI() {
    if (!cartContainer || !subtotalEl || !diskonEl || !totalEl || !changeEl) {
        return;
    }

    if (cart.length === 0) {
        cartContainer.innerHTML = '<p class="empty-text">Belum ada menu yang dipilih</p>';
        subtotalEl.innerText = formatRupiah(0);
        diskonEl.innerText = "- " + formatRupiah(0);
        totalEl.innerText = formatRupiah(0);
        changeEl.innerText = formatRupiah(0);

        if (cashInput) {
            cashInput.value = '';
        }

        return;
    }

    cartContainer.innerHTML = "";

    let subtotal = 0;

    cart.forEach(item => {
        const itemSubtotal = item.harga * item.qty;
        subtotal += itemSubtotal;

        const div = document.createElement('div');
        div.className = 'item-cart';

        div.innerHTML = `
            <div>
                <span class="cart-code">${item.id}</span>
                <h4 class="cart-name">${item.nama}</h4>

                <div class="qty-control">
                    <button type="button" class="qty-btn" onclick="changeQty('${item.id}', -1)">-</button>
                    <span class="qty-number">${item.qty}</span>
                    <button type="button" class="qty-btn" onclick="changeQty('${item.id}', 1)">+</button>
                </div>
            </div>

            <div class="cart-price">
                ${formatRupiah(itemSubtotal)}
            </div>
        `;

        cartContainer.appendChild(div);
    });

    const diskon = Math.round(subtotal * (discountPercent / 100));
    const total = subtotal - diskon;

    subtotalEl.innerText = formatRupiah(subtotal);
    diskonEl.innerText = "- " + formatRupiah(diskon);
    totalEl.innerText = formatRupiah(total);

    calculateChange(total);
}


// Tambah / kurang qty
window.changeQty = function(id, delta) {
    const item = cart.find(i => i.id === id);

    if (!item) return;

    item.qty += delta;

    if (item.qty <= 0) {
        cart = cart.filter(i => i.id !== id);
    }

    updateCartUI();
};


// ======================================================
// 3. HITUNG KEMBALIAN
// ======================================================

if (cashInput) {
    cashInput.addEventListener('input', function() {
        const total = getTotalFromUI();
        calculateChange(total);
    });
}


function getTotalFromUI() {
    if (!totalEl) return 0;
    return parseInt(totalEl.innerText.replace(/[^\d]/g, '')) || 0;
}


function calculateChange(totalHarga) {
    if (!cashInput || !changeEl) return;

    const cashPaid = parseInt(cashInput.value) || 0;
    const change = cashPaid - totalHarga;

    changeEl.innerText = change >= 0 ? formatRupiah(change) : formatRupiah(0);
}


// ======================================================
// 4. METODE PEMBAYARAN
// ======================================================

const methodButtons = document.querySelectorAll('.method-btn');

if (methodButtons.length > 0) {
    methodButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            methodButtons.forEach(b => b.classList.remove('active'));

            this.classList.add('active');
            selectedMethod = this.dataset.method || "CASH";

            if (cashInput) {
                if (selectedMethod === "CASH") {
                    cashInput.disabled = false;
                    cashInput.placeholder = "Masukkan nominal uang";
                } else {
                    cashInput.value = "";
                    cashInput.disabled = true;
                    cashInput.placeholder = "Tidak perlu input tunai";
                    calculateChange(getTotalFromUI());
                }
            }
        });
    });
}


// ======================================================
// 5. PROSES PEMBAYARAN
// ======================================================

const btnProses = document.getElementById('btn-proses-bayar');

if (btnProses) {
    btnProses.addEventListener('click', async function() {
        if (cart.length === 0) {
            alert("Keranjang belanja masih kosong!");
            return;
        }

        const custNameInput = document.getElementById('cust-name');
        const custTableInput = document.getElementById('cust-table');

        const custName = custNameInput ? custNameInput.value.trim() || "General Customer" : "General Customer";
        const custTable = custTableInput ? custTableInput.value.trim() || "TA" : "TA";

        const totalHarga = getTotalFromUI();
        const cashPaid = cashInput ? parseInt(cashInput.value) || 0 : 0;

        if (selectedMethod === "CASH" && cashPaid < totalHarga) {
            alert("Uang tunai yang dibayarkan masih kurang!");
            return;
        }

        const transaksi = {
            customer: custName,
            meja: custTable,
            items: cart,
            subtotal: cart.reduce((sum, item) => sum + (item.harga * item.qty), 0),
            diskon_persen: discountPercent,
            total: totalHarga,
            bayar: selectedMethod === "CASH" ? cashPaid : totalHarga,
            kembalian: selectedMethod === "CASH" ? cashPaid - totalHarga : 0,
            metode: selectedMethod
        };

        btnProses.disabled = true;
        btnProses.innerText = "Memproses...";

        try {
            const response = await fetch('/api/transaksi', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(transaksi)
            });

            const data = await response.json();

            if (data.status === 'success') {
                alert(data.message || "Pembayaran berhasil diproses!");

                resetCart();
            } else {
                alert(data.message || "Transaksi gagal diproses.");
            }

        } catch (error) {
            console.error("Error Transaksi:", error);
            alert("Terjadi kesalahan saat memproses transaksi.");

        } finally {
            btnProses.disabled = false;
            btnProses.innerText = "Proses Pembayaran";
        }
    });
}


// ======================================================
// 6. RESET KERANJANG
// ======================================================

const btnReset = document.getElementById('btn-reset-cart');

if (btnReset) {
    btnReset.addEventListener('click', function() {
        resetCart();
    });
}


function resetCart() {
    cart = [];

    if (cashInput) cashInput.value = '';

    const custNameInput = document.getElementById('cust-name');
    const custTableInput = document.getElementById('cust-table');

    if (custNameInput) custNameInput.value = '';
    if (custTableInput) custTableInput.value = '';

    updateCartUI();
}


// Jalankan saat halaman kasir pertama kali dibuka
updateCartUI();