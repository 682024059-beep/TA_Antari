// ======================================================
// ANTARI COFFEE - MAIN JAVASCRIPT
// ======================================================

let cart = [];
let discountPercent = 0;
let selectedMethod = "";

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

        .receipt-meta,
        .receipt-items,
        .receipt-total {
            padding: 18px 0;
            border-bottom: 1px dashed #d9c6bb;
        }

        .receipt-meta,
        .receipt-total {
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
// 2. ELEMENT KASIR
// ======================================================

const gridProduk = document.querySelector(".grid-produk");
const cartContainer = document.getElementById("cart-items");
const subtotalEl = document.getElementById("subtotal-val");
const diskonEl = document.getElementById("diskon-val");
const totalEl = document.getElementById("total-val");
const cashInput = document.getElementById("cash-input");
const changeEl = document.getElementById("change-val");
const custNameInput = document.getElementById("cust-name");
const btnProses = document.getElementById("btn-proses-bayar");
const btnReset = document.getElementById("btn-reset-cart");
const diskonRow = diskonEl ? diskonEl.closest(".summary-line") : null;
const methodButtons = document.querySelectorAll(".method-btn");

// ======================================================
// 3. VALIDASI DAN HELPER
// ======================================================

function getTotalFromUI() {
    if (!totalEl) return 0;
    return parseInt(totalEl.innerText.replace(/[^\d]/g, "")) || 0;
}

function getCashPaidValue() {
    if (!cashInput) return 0;

    const value = parseInt(cashInput.value) || 0;

    if (value < 0) {
        cashInput.value = "";
        return 0;
    }

    return value;
}

function preventMinusCashInput() {
    if (!cashInput) return;

    cashInput.setAttribute("min", "0");
    cashInput.setAttribute("step", "1000");

    cashInput.addEventListener("keydown", function(e) {
        if (e.key === "-" || e.key === "+" || e.key.toLowerCase() === "e") {
            e.preventDefault();
        }
    });

    cashInput.addEventListener("input", function() {
        const value = parseInt(cashInput.value) || 0;

        if (value < 0) {
            cashInput.value = "";
        }
    });
}

function updateDiscountDisplay() {
    if (!diskonRow) return;

    if (discountPercent <= 0) {
        diskonRow.style.display = "none";
    } else {
        diskonRow.style.display = "flex";
    }
}

function updatePaymentMethodUI() {
    methodButtons.forEach(function(button) {
        const method = button.dataset.method;

        if (method === selectedMethod) {
            button.classList.add("active");
        } else {
            button.classList.remove("active");
        }
    });

    const totalHarga = getTotalFromUI();

    if (cashInput) {
        if (selectedMethod === "QRIS") {
            cashInput.value = totalHarga > 0 ? totalHarga : "";
            cashInput.disabled = true;
            calculateChange(totalHarga);
        } else {
            cashInput.disabled = false;
        }
    }
}

function selectPaymentMethod(method) {
    selectedMethod = method;

    if (selectedMethod === "Cash") {
        if (cashInput) {
            cashInput.disabled = false;
            cashInput.value = "";
        }
    }

    if (selectedMethod === "QRIS") {
        const totalHarga = getTotalFromUI();

        if (cashInput) {
            cashInput.value = totalHarga > 0 ? totalHarga : "";
            cashInput.disabled = true;
        }

        calculateChange(totalHarga);
    }

    updatePaymentMethodUI();
    validatePaymentButton();
}

function resetPaymentMethod() {
    selectedMethod = "";

    methodButtons.forEach(function(button) {
        button.classList.remove("active");
    });

    if (cashInput) {
        cashInput.disabled = false;
        cashInput.value = "";
    }
}

function isPaymentComplete(showAlert = false) {
    const namaCustomer = custNameInput ? custNameInput.value.trim() : "";
    const totalHarga = getTotalFromUI();
    const jumlahDibayar = getCashPaidValue();

    if (!namaCustomer) {
        if (showAlert) alert("Nama customer wajib diisi!");
        return false;
    }

    if (cart.length === 0) {
        if (showAlert) alert("Detail pesanan masih kosong!");
        return false;
    }

    if (totalHarga <= 0) {
        if (showAlert) alert("Total harga belum valid!");
        return false;
    }

    if (!selectedMethod) {
        if (showAlert) alert("Pilih metode pembayaran Cash atau QRIS!");
        return false;
    }

    if (selectedMethod === "Cash") {
        if (jumlahDibayar <= 0) {
            if (showAlert) alert("Jumlah dibayar wajib diisi!");
            return false;
        }

        if (jumlahDibayar < totalHarga) {
            if (showAlert) alert("Jumlah dibayar masih kurang!");
            return false;
        }
    }

    if (selectedMethod === "QRIS") {
        if (totalHarga <= 0) {
            if (showAlert) alert("Total QRIS belum valid!");
            return false;
        }
    }

    return true;
}

function validatePaymentButton() {
    if (!btnProses) return;
    btnProses.disabled = !isPaymentComplete(false);
}

// ======================================================
// 4. KERANJANG KASIR
// ======================================================

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

        updateDiscountDisplay();
        updatePaymentMethodUI();
        validatePaymentButton();
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

    const diskon = discountPercent > 0
        ? Math.round(subtotal * (discountPercent / 100))
        : 0;

    const total = subtotal - diskon;

    subtotalEl.innerText = formatRupiah(subtotal);
    diskonEl.innerText = "- " + formatRupiah(diskon);
    totalEl.innerText = formatRupiah(total);

    if (selectedMethod === "QRIS" && cashInput) {
        cashInput.value = total;
    }

    calculateChange(total);
    updateDiscountDisplay();
    updatePaymentMethodUI();
    validatePaymentButton();
}

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
// 5. HITUNG KEMBALIAN
// ======================================================

if (cashInput) {
    cashInput.addEventListener("input", function() {
        const total = getTotalFromUI();
        calculateChange(total);
        validatePaymentButton();
    });
}

if (custNameInput) {
    custNameInput.addEventListener("input", validatePaymentButton);
}

methodButtons.forEach(function(button) {
    button.addEventListener("click", function() {
        const method = button.dataset.method;
        selectPaymentMethod(method);
    });
});

function calculateChange(totalHarga) {
    if (!cashInput || !changeEl) return;

    if (selectedMethod === "QRIS") {
        changeEl.innerText = formatRupiah(0);
        return;
    }

    const cashPaid = getCashPaidValue();
    const change = cashPaid - totalHarga;

    changeEl.innerText = change >= 0 ? formatRupiah(change) : formatRupiah(0);
}

// ======================================================
// 6. STRUK POPUP
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

function buildReceiptDiscountLine(transaksi) {
    if (!transaksi.diskon || transaksi.diskon <= 0) return "";

    return `
        <div class="receipt-line">
            <span>Diskon (${transaksi.diskon_persen}%)</span>
            <strong>- ${formatRupiah(transaksi.diskon)}</strong>
        </div>
    `;
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
                </div>

                <div class="receipt-items">
                    ${buildReceiptItems(transaksi.items)}
                </div>

                <div class="receipt-total">
                    <div class="receipt-line">
                        <span>Subtotal</span>
                        <strong>${formatRupiah(transaksi.subtotal)}</strong>
                    </div>

                    ${buildReceiptDiscountLine(transaksi)}

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
// 7. PROSES PEMBAYARAN
// ======================================================

if (btnProses) {
    btnProses.addEventListener("click", async function() {
        if (!isPaymentComplete(true)) {
            validatePaymentButton();
            return;
        }

        const usernameEl = document.querySelector(".avatar-box h4");

        const custName = custNameInput ? custNameInput.value.trim() : "";
        const kasirName = usernameEl ? usernameEl.innerText.trim() || "Kasir" : "Kasir";

        const subtotal = cart.reduce((sum, item) => sum + (item.harga * item.qty), 0);

        const diskon = discountPercent > 0
            ? Math.round(subtotal * (discountPercent / 100))
            : 0;

        const totalHarga = subtotal - diskon;

        let finalBayar = 0;
        let finalKembalian = 0;

        if (selectedMethod === "QRIS") {
            finalBayar = totalHarga;
            finalKembalian = 0;
        } else {
            finalBayar = getCashPaidValue();
            finalKembalian = finalBayar - totalHarga;
        }

        const paymentLabel = selectedMethod;

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
            btnProses.innerText = "Proses Pembayaran";
            validatePaymentButton();
        }
    });
}

// ======================================================
// 8. RESET KERANJANG
// ======================================================

if (btnReset) {
    btnReset.addEventListener("click", function() {
        resetCart();
    });
}

function resetCart() {
    cart = [];

    if (cashInput) {
        cashInput.disabled = false;
        cashInput.value = "";
    }

    if (custNameInput) {
        custNameInput.value = "";
    }

    resetPaymentMethod();
    updateCartUI();
    validatePaymentButton();
}

// ======================================================
// 9. PENCARIAN, FILTER KATEGORI, DAN NOTIFIKASI
// ======================================================

const searchProdukInput = document.getElementById("searchProduk");
const kategoriButtons = document.querySelectorAll(".kat-btn");
const productCards = document.querySelectorAll(".card-produk");
const bellIcon = document.querySelector(".icon-bell");

let activeCategory = "semua";

function normalizeText(text) {
    return String(text || "").toLowerCase().trim();
}

function filterProduk() {
    const keyword = searchProdukInput ? normalizeText(searchProdukInput.value) : "";

    productCards.forEach(function(card) {
        const nama = normalizeText(card.dataset.nama);
        const kode = normalizeText(card.dataset.id);
        const kategori = normalizeText(card.dataset.kategori);

        const cocokSearch =
            !keyword ||
            nama.includes(keyword) ||
            kode.includes(keyword) ||
            kategori.includes(keyword);

        const cocokKategori =
            activeCategory === "semua" ||
            kategori === normalizeText(activeCategory);

        card.style.display = cocokSearch && cocokKategori ? "" : "none";
    });
}

if (searchProdukInput) {
    searchProdukInput.disabled = false;

    searchProdukInput.addEventListener("input", function() {
        filterProduk();
    });
}

kategoriButtons.forEach(function(button) {
    button.addEventListener("click", function() {
        if (button.disabled) return;

        kategoriButtons.forEach(function(btn) {
            btn.classList.remove("active");
        });

        button.classList.add("active");
        activeCategory = button.dataset.category || "semua";

        filterProduk();
    });
});

// ---------- Helper aman untuk teks ----------
function escapeHtml(value) {
    return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

// ---------- Helper waktu notifikasi ----------
function parseNotifDate(value) {
    if (!value) return null;

    let s = String(value).trim();

    // Kalau backend masih mengirim format mentah begini, berarti waktunya tidak valid
    if (
        s.includes("%d") ||
        s.includes("%m") ||
        s.includes("%Y") ||
        s.includes("%H") ||
        s.includes("%i")
    ) {
        return null;
    }

    // Format ISO: 2026-07-09T20:35:40
    if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(s)) {
        return new Date(s);
    }

    // Format MySQL/TiDB: 2026-07-09 20:35:40
    // Ini dianggap waktu lokal, bukan UTC, supaya tidak selisih 7 jam.
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(s)) {
        s = s.replace(" ", "T");
        return new Date(s);
    }

    // Format Indonesia: 09/07/2026 20:35
    if (/^\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}/.test(s)) {
        const [datePart, timePart] = s.split(" ");
        const [day, month, year] = datePart.split("/");
        return new Date(`${year}-${month}-${day}T${timePart}:00`);
    }

    const date = new Date(s);
    return isNaN(date.getTime()) ? null : date;
}

function formatNotifTime(value) {
    const date = parseNotifDate(value);

    if (!date) {
        return "";
    }

    let diff = Date.now() - date.getTime();

    if (diff < 0) {
        diff = 0;
    }

    const detik = Math.floor(diff / 1000);
    const menit = Math.floor(detik / 60);
    const jam = Math.floor(menit / 60);
    const hari = Math.floor(jam / 24);

    if (detik < 10) return "baru saja";
    if (detik < 60) return `${detik} detik lalu`;
    if (menit < 60) return `${menit} menit lalu`;
    if (jam < 24) return `${jam} jam lalu`;
    if (hari === 1) return "kemarin";
    if (hari < 7) return `${hari} hari lalu`;

    return date.toLocaleDateString("id-ID", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
}

function isUnreadNotif(item) {
    return (
        item.is_read === 0 ||
        item.is_read === false ||
        item.is_read === "0" ||
        item.is_read === null
    );
}

function getNotifIcon(tipe) {
    if (tipe === "stok_menipis" || tipe === "stok_habis") {
        return '<i class="fa-solid fa-triangle-exclamation"></i>';
    }

    if (tipe === "produk_hapus") {
        return '<i class="fa-solid fa-trash"></i>';
    }

    if (tipe === "produk_update") {
        return '<i class="fa-solid fa-pen"></i>';
    }

    if (tipe === "produk_baru") {
        return '<i class="fa-solid fa-box"></i>';
    }

    return '<i class="fa-solid fa-bell"></i>';
}

// ---------- Setup lonceng notifikasi ----------
function setupNotificationBell() {
    if (!bellIcon) return;

    if (bellIcon.parentElement && bellIcon.parentElement.classList.contains("notification-wrapper")) {
        return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "notification-wrapper";

    bellIcon.parentNode.insertBefore(wrapper, bellIcon);
    wrapper.appendChild(bellIcon);

    const badge = document.createElement("span");
    badge.className = "notification-badge";
    badge.id = "notificationBadge";
    badge.style.display = "none";
    wrapper.appendChild(badge);

    const dropdown = document.createElement("div");
    dropdown.className = "notification-dropdown";
    dropdown.id = "notificationDropdown";
    dropdown.style.display = "none";
    dropdown.innerHTML = `
        <div class="notification-head">
            <strong>Notifikasi</strong>
        </div>
        <div class="notification-list" id="notificationList">
            <p class="notification-empty">Belum ada notifikasi baru.</p>
        </div>
    `;
    wrapper.appendChild(dropdown);

    function toggleDropdown() {
        const isOpen = dropdown.style.display === "block";

        if (isOpen) {
            dropdown.style.display = "none";
        } else {
            dropdown.style.display = "block";
            loadNotifications();
            markNotificationsAsRead();
        }
    }

    wrapper.addEventListener("click", function(e) {
        e.stopPropagation();
        toggleDropdown();
    });

    dropdown.addEventListener("click", function(e) {
        e.stopPropagation();
    });

    document.addEventListener("click", function() {
        dropdown.style.display = "none";
    });

    loadNotifications();
    setInterval(loadNotifications, 10000);
}

async function loadNotifications() {
    const badge = document.getElementById("notificationBadge");
    const list = document.getElementById("notificationList");

    if (!badge || !list) return;

    try {
        const response = await fetch("/api/notifikasi/kasir");
        const data = await response.json();

        if (data.status !== "success") {
            list.innerHTML = `<p class="notification-empty">Gagal memuat notifikasi.</p>`;
            return;
        }

        const notifications = data.data || [];

        const unreadCount = notifications.filter(function(item) {
            return isUnreadNotif(item);
        }).length;

        if (unreadCount > 0) {
            badge.innerText = unreadCount > 99 ? "99+" : unreadCount;
            badge.style.display = "inline-flex";
        } else {
            badge.style.display = "none";
        }

        if (notifications.length === 0) {
            list.innerHTML = `<p class="notification-empty">Belum ada notifikasi baru.</p>`;
            return;
        }

        list.innerHTML = notifications.map(function(item) {
            const unreadClass = isUnreadNotif(item) ? "unread" : "";

            return `
                <div class="notification-item ${unreadClass}" data-id="${escapeHtml(item.id)}">
                    <div class="notification-icon">
                        ${getNotifIcon(item.tipe)}
                    </div>

                    <div class="notification-body">
                        <strong>${escapeHtml(item.judul || "Notifikasi")}</strong>
                        <p>${escapeHtml(item.pesan || "-")}</p>
                        <small>${formatNotifTime(item.created_at)}</small>
                    </div>
                </div>
            `;
        }).join("");

    } catch (error) {
        console.error("Gagal mengambil notifikasi:", error);
        list.innerHTML = `<p class="notification-empty">Gagal memuat notifikasi.</p>`;
    }
}

async function markNotificationsAsRead() {
    const badge = document.getElementById("notificationBadge");

    try {
        await fetch("/api/notifikasi/kasir/read", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        });

        if (badge) {
            badge.style.display = "none";
        }

    } catch (error) {
        console.error("Gagal menandai notifikasi:", error);
    }
}

// ======================================================
// 9. INIT
// ======================================================

preventMinusCashInput();
updateCartUI();
updateDiscountDisplay();
updatePaymentMethodUI();
validatePaymentButton();
filterProduk();
setupNotificationBell();