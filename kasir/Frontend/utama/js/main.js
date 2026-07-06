// ======================================================
// ANTARI COFFEE - MAIN JAVASCRIPT
// ======================================================

// Global State Keranjang
let cart = [];
let discountPercent = 10;

// Karena metode pembayaran dihapus dari UI,
// sistem pakai default internal agar backend tidak error.
let selectedMethod = "QRIS Eksternal";


// Format angka ke Rupiah
function formatRupiah(angka) {
    return `Rp ${Number(angka || 0).toLocaleString("id-ID")}`;
}


// ======================================================
// 0. STYLE POPUP STRUK
// ======================================================

(function injectReceiptStyle() {
    if (document.getElementById("receiptModalStyle")) return;

    const style = document.createElement("style");
    style.id = "receiptModalStyle";
    style.innerHTML = `
        .receipt-overlay {
            position: fixed;
            inset: 0;
            z-index: 9999;
            background: rgba(28, 18, 15, 0.55);
            backdrop-filter: blur(6px);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 22px;
        }

        .receipt-modal {
            width: min(430px, 100%);
            max-height: 92vh;
            overflow-y: auto;
            background: #fffaf7;
            border-radius: 20px;
            border: 1px solid #ead8cf;
            box-shadow: 0 24px 70px rgba(36, 22, 20, 0.28);
        }

        .receipt-paper {
            padding: 28px;
            color: #251916;
        }

        .receipt-header {
            text-align: center;
            padding-bottom: 18px;
            border-bottom: 1px dashed #d9c6bb;
        }

        .receipt-header h2 {
            font-size: 24px;
            font-weight: 900;
            margin-bottom: 4px;
        }

        .receipt-header p {
            color: #8b7b75;
            font-size: 12px;
            font-weight: 700;
        }

        .receipt-meta {
            padding: 18px 0;
            border-bottom: 1px dashed #d9c6bb;
            display: grid;
            gap: 8px;
        }

        .receipt-line {
            display: flex;
            justify-content: space-between;
            gap: 14px;
            font-size: 13px;
            color: #4f403b;
        }

        .receipt-line span:first-child {
            color: #8b7b75;
            font-weight: 800;
        }

        .receipt-line strong {
            text-align: right;
            font-weight: 900;
        }

        .receipt-items {
            padding: 18px 0;
            border-bottom: 1px dashed #d9c6bb;
        }

        .receipt-item {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 12px;
            margin-bottom: 12px;
            font-size: 13px;
        }

        .receipt-item:last-child {
            margin-bottom: 0;
        }

        .receipt-item-name {
            font-weight: 900;
            color: #251916;
        }

        .receipt-item-sub {
            margin-top: 2px;
            color: #8b7b75;
            font-size: 12px;
            font-weight: 700;
        }

        .receipt-item-price {
            font-weight: 900;
            color: #7a3e08;
            white-space: nowrap;
        }

        .receipt-total {
            padding: 18px 0;
            display: grid;
            gap: 10px;
            border-bottom: 1px dashed #d9c6bb;
        }

        .receipt-grand {
            margin-top: 6px;
            padding-top: 12px;
            border-top: 1px solid #ead8cf;
            font-size: 18px;
        }

        .receipt-grand strong {
            color: #7a3e08;
        }

        .receipt-footer {
            padding-top: 18px;
            text-align: center;
            color: #8b7b75;
            font-size: 12px;
            font-weight: 700;
            line-height: 1.6;
        }

        .receipt-actions {
            display: flex;
            gap: 12px;
            padding: 18px 28px 28px;
        }

        .receipt-btn {
            flex: 1;
            min-height: 46px;
            border: none;
            border-radius: 14px;
            font-weight: 900;
            cursor: pointer;
        }

        .receipt-btn.print {
            background: linear-gradient(135deg, #7a3e08, #a55c16);
            color: #ffffff;
        }

        .receipt-btn.close {
            background: #eadfd8;
            color: #4f403b;
        }

        @media print {
            body > *:not(.receipt-overlay) {
                display: none !important;
            }

            .receipt-overlay {
                position: static;
                background: #ffffff;
                padding: 0;
                display: block;
            }

            .receipt-modal {
                width: 100%;
                max-height: none;
                box-shadow: none;
                border: none;
                border-radius: 0;
            }

            .receipt-actions {
                display: none;
            }
        }
    `;

    document.head.appendChild(style);
})();


// ======================================================
// 1. LOGIN PAGE
// ======================================================

const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const togglePassword = document.getElementById("togglePassword");

if (loginForm) {
    loginForm.addEventListener("submit", async function(e) {
        e.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();
        const btnLogin = document.getElementById("btn-login-submit");

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
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });

            const data = await response.json();

            if (data.status === "success") {
                if (loginMessage) {
                    loginMessage.textContent = data.message || "Login berhasil.";
                    loginMessage.className = "login-message success";
                }

                setTimeout(() => {
                    window.location.href = data.redirect || "/kasir";
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
    togglePassword.addEventListener("click", function() {
        const passwordInput = document.getElementById("password");

        if (!passwordInput) return;

        if (passwordInput.type === "password") {
            passwordInput.type = "text";
            this.classList.remove("fa-eye");
            this.classList.add("fa-eye-slash");
        } else {
            passwordInput.type = "password";
            this.classList.remove("fa-eye-slash");
            this.classList.add("fa-eye");
        }
    });
}


// ======================================================
// 2. KERANJANG KASIR
// ======================================================

const gridProduk = document.querySelector(".grid-produk");
const cartContainer = document.getElementById("cart-items");
const subtotalEl = document.getElementById("subtotal-val");
const diskonEl = document.getElementById("diskon-val");
const totalEl = document.getElementById("total-val");
const cashInput = document.getElementById("cash-input");
const changeEl = document.getElementById("change-val");


// Klik produk untuk masuk keranjang
if (gridProduk) {
    gridProduk.addEventListener("click", function(e) {
        const card = e.target.closest(".card-produk");

        if (!card) return;

        if (card.classList.contains("stok-habis")) {
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
            cashInput.value = "";
        }

        return;
    }

    cartContainer.innerHTML = "";

    let subtotal = 0;

    cart.forEach(item => {
        const itemSubtotal = item.harga * item.qty;
        subtotal += itemSubtotal;

        const div = document.createElement("div");
        div.className = "item-cart";

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
    cashInput.addEventListener("input", function() {
        const total = getTotalFromUI();
        calculateChange(total);
    });
}


function getTotalFromUI() {
    if (!totalEl) return 0;
    return parseInt(totalEl.innerText.replace(/[^\d]/g, "")) || 0;
}


function calculateChange(totalHarga) {
    if (!cashInput || !changeEl) return;

    const cashPaid = parseInt(cashInput.value) || 0;
    const change = cashPaid - totalHarga;

    changeEl.innerText = change >= 0 ? formatRupiah(change) : formatRupiah(0);
}


// ======================================================
// 4. STRUK POPUP
// ======================================================

function buildReceiptItems(items) {
    return items.map(item => {
        const itemSubtotal = item.harga * item.qty;

        return `
            <div class="receipt-item">
                <div>
                    <div class="receipt-item-name">${item.nama}</div>
                    <div class="receipt-item-sub">${item.qty} x ${formatRupiah(item.harga)}</div>
                </div>
                <div class="receipt-item-price">${formatRupiah(itemSubtotal)}</div>
            </div>
        `;
    }).join("");
}


function showReceiptPopup(transaksi) {
    const oldModal = document.querySelector(".receipt-overlay");
    if (oldModal) oldModal.remove();

    const overlay = document.createElement("div");
    overlay.className = "receipt-overlay";

    overlay.innerHTML = `
        <div class="receipt-modal">
            <div class="receipt-paper">
                <div class="receipt-header">
                    <h2>Antari Coffee</h2>
                    <p>Struk Transaksi Kasir</p>
                </div>

                <div class="receipt-meta">
                    <div class="receipt-line">
                        <span>No Transaksi</span>
                        <strong>${transaksi.no}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Tanggal</span>
                        <strong>${transaksi.tanggal}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Waktu</span>
                        <strong>${transaksi.waktu}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Kasir</span>
                        <strong>${transaksi.kasir}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Customer</span>
                        <strong>${transaksi.customer}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Meja</span>
                        <strong>${transaksi.meja}</strong>
                    </div>
                </div>

                <div class="receipt-items">
                    ${buildReceiptItems(transaksi.items)}
                </div>

                <div class="receipt-total">
                    <div class="receipt-line">
                        <span>Subtotal</span>
                        <strong>${formatRupiah(transaksi.subtotal)}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Diskon (${transaksi.diskon_persen}%)</span>
                        <strong>- ${formatRupiah(transaksi.diskon)}</strong>
                    </div>
                    <div class="receipt-line receipt-grand">
                        <span>Total</span>
                        <strong>${formatRupiah(transaksi.total)}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Dibayar</span>
                        <strong>${formatRupiah(transaksi.bayar)}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Kembalian</span>
                        <strong>${formatRupiah(transaksi.kembalian)}</strong>
                    </div>
                    <div class="receipt-line">
                        <span>Pembayaran</span>
                        <strong>${transaksi.metode}</strong>
                    </div>
                </div>

                <div class="receipt-footer">
                    <p>Terima kasih telah berkunjung.</p>
                    <p>Simpan struk ini sebagai bukti transaksi.</p>
                </div>
            </div>

            <div class="receipt-actions">
                <button type="button" class="receipt-btn close" id="closeReceiptBtn">
                    Tutup
                </button>
                <button type="button" class="receipt-btn print" id="printReceiptBtn">
                    Cetak Struk
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById("closeReceiptBtn").addEventListener("click", function() {
        overlay.remove();
        resetCart();
    });

    document.getElementById("printReceiptBtn").addEventListener("click", function() {
        window.print();
    });
}


// ======================================================
// 5. PROSES PEMBAYARAN
// ======================================================

const btnProses = document.getElementById("btn-proses-bayar");

if (btnProses) {
    btnProses.addEventListener("click", async function() {
        if (cart.length === 0) {
            alert("Keranjang belanja masih kosong!");
            return;
        }

        const custNameInput = document.getElementById("cust-name");
        const custTableInput = document.getElementById("cust-table");
        const usernameEl = document.querySelector(".avatar-box h4");

        const custName = custNameInput ? custNameInput.value.trim() || "General Customer" : "General Customer";
        const custTable = custTableInput ? custTableInput.value.trim() || "TA" : "TA";
        const kasirName = usernameEl ? usernameEl.innerText.trim() || "Kasir" : "Kasir";

        const subtotal = cart.reduce((sum, item) => sum + (item.harga * item.qty), 0);
        const diskon = Math.round(subtotal * (discountPercent / 100));
        const totalHarga = subtotal - diskon;

        let cashPaid = cashInput ? parseInt(cashInput.value) || 0 : 0;

        // Jika jumlah dibayar kosong, dianggap QRIS/cashless eksternal.
        // Maka otomatis lunas sesuai total.
        let paymentLabel = "QRIS Eksternal";
        let finalBayar = totalHarga;
        let finalKembalian = 0;

        // Jika kasir mengisi nominal, sistem menganggap pembayaran tunai.
        if (cashPaid > 0) {
            if (cashPaid < totalHarga) {
                alert("Jumlah dibayar masih kurang!");
                return;
            }

            paymentLabel = "Cash";
            finalBayar = cashPaid;
            finalKembalian = cashPaid - totalHarga;
        }

        const now = new Date();
        const tanggal = now.toLocaleDateString("id-ID");
        const waktu = now.toLocaleTimeString("id-ID", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });

        const noTransaksiLocal = `TRX-${now.getTime().toString().slice(-6)}`;

        const transaksi = {
            no: noTransaksiLocal,
            customer: custName,
            meja: custTable,
            items: cart.map(item => ({ ...item })),
            subtotal: subtotal,
            diskon: diskon,
            diskon_persen: discountPercent,
            total: totalHarga,
            bayar: finalBayar,
            kembalian: finalKembalian,
            metode: paymentLabel,
            tanggal: tanggal,
            waktu: waktu,
            kasir: kasirName
        };

        btnProses.disabled = true;
        btnProses.innerText = "Memproses...";

        try {
            const response = await fetch("/api/transaksi", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(transaksi)
            });

            const data = await response.json();

            if (data.status === "success") {
                transaksi.no = data.no || data.no_transaksi || data.id_transaksi || transaksi.no;

                showReceiptPopup(transaksi);
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

const btnReset = document.getElementById("btn-reset-cart");

if (btnReset) {
    btnReset.addEventListener("click", function() {
        resetCart();
    });
}


function resetCart() {
    cart = [];

    if (cashInput) cashInput.value = "";

    const custNameInput = document.getElementById("cust-name");
    const custTableInput = document.getElementById("cust-table");

    if (custNameInput) custNameInput.value = "";
    if (custTableInput) custTableInput.value = "";

    updateCartUI();
}


// Jalankan saat halaman kasir pertama kali dibuka
updateCartUI();