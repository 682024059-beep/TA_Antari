/**
 * penjualan.js
 * Logika halaman "Riwayat Penjualan":
 *  - Tab Harian / Mingguan / Bulanan + date-picker custom
 *  - Kartu statistik (total transaksi, pendapatan, cash, cashless)
 *  - Grafik pendapatan per hari (Chart.js)
 *  - Daftar produk terlaris
 *  - Tabel transaksi dengan pencarian & pagination
 *  - Export Excel
 */

let state = { range: "harian", start: "", end: "", search: "", page: 1 };
let penjualanChart = null;
let timerSearch = null;

function buildQuery() {
  const params = new URLSearchParams();
  params.set("range", state.range);
  if (state.start) params.set("start", state.start);
  if (state.end) params.set("end", state.end);
  if (state.search) params.set("search", state.search);
  params.set("page", state.page);
  params.set("per_page", 4);
  return params.toString();
}

async function muatPenjualan() {
  try {
    const data = await apiFetch(`/api/penjualan?${buildQuery()}`);

    // sinkronkan date-picker dengan periode aktif (kalau user belum override manual)
    document.getElementById("filter-start").value = data.periode.start;
    document.getElementById("filter-end").value = data.periode.end;
    document.getElementById("periode-label").textContent =
      `${formatTanggalSingkat(data.periode.start)} - ${formatTanggalSingkat(data.periode.end)}`;

    renderStats(data.ringkasan);
    renderChart(data.grafik);
    renderTopProduk(data.produk_terlaris);
    renderTransaksi(data.transaksi);
    renderPagination(data.pagination);
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderStats(r) {
  const el = document.getElementById("penjualan-stats");
  const naik = (v) => (v >= 0 ? "+" : "") + v + "% vs periode lalu";
  el.innerHTML = `
    <div class="card stat-card">
      <div class="stat-icon tone-rose"><i data-lucide="receipt"></i></div>
      <div class="card-eyebrow">Total Transaksi</div>
      <div class="card-value">${r.total_transaksi.toLocaleString("id-ID")}</div>
      <div class="card-trend up"><i data-lucide="trending-up"></i> ${naik(r.perubahan_transaksi)}</div>
    </div>
    <div class="card stat-card">
      <div class="stat-icon tone-brown"><i data-lucide="banknote"></i></div>
      <div class="card-eyebrow">Total Pendapatan</div>
      <div class="card-value">${formatRupiahSingkat(r.total_pendapatan)}</div>
      <div class="card-trend up"><i data-lucide="trending-up"></i> ${naik(r.perubahan_pendapatan)}</div>
    </div>
    <div class="card stat-card">
      <div class="stat-icon tone-orange"><i data-lucide="wallet"></i></div>
      <div class="card-eyebrow">Metode Cash</div>
      <div class="card-value">${formatRupiahSingkat(r.metode_cash)}</div>
      <div class="stat-meter"><div style="width:${pct(r.metode_cash, r.total_pendapatan)}%;background:#c0772b;"></div></div>
    </div>
    <div class="card stat-card">
      <div class="stat-icon tone-blue"><i data-lucide="credit-card"></i></div>
      <div class="card-eyebrow">Metode Cashless</div>
      <div class="card-value">${formatRupiahSingkat(r.metode_cashless)}</div>
      <div class="stat-meter"><div style="width:${pct(r.metode_cashless, r.total_pendapatan)}%;background:#2563eb;"></div></div>
    </div>
  `;
  refreshIcons();
}

function pct(value, total) {
  if (!total) return 0;
  return Math.min(Math.round((value / total) * 100), 100);
}

function renderChart(grafik) {
  const ctx = document.getElementById("penjualan-chart");
  if (penjualanChart) penjualanChart.destroy();
  penjualanChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: grafik.labels,
      datasets: [
        {
          label: "Pendapatan",
          data: grafik.values,
          backgroundColor: "#8b2e22",
          borderRadius: 6,
          maxBarThickness: 30,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { callback: (v) => formatRupiahSingkat(v) }, grid: { color: "#f0eae6" } },
        x: { grid: { display: false } },
      },
    },
  });
}

function renderTopProduk(list) {
  const el = document.getElementById("rank-list");
  if (list.length === 0) {
    el.innerHTML = `<p class="empty-state">Belum ada data penjualan produk pada periode ini.</p>`;
    return;
  }
  el.innerHTML = list
    .map(
      (p, i) => `
      <div class="rank-item">
        <span class="rank-num">${i + 1}</span>
        <div class="rank-info">
          <div class="name">${p.nama}</div>
          <div class="sub">${p.qty} Terjual</div>
        </div>
        <span class="rank-percent">${p.persen}%</span>
      </div>
    `
    )
    .join("");
}

function renderTransaksi(list) {
  const tbody = document.getElementById("transaksi-tbody");
  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Tidak ada transaksi ditemukan.</td></tr>`;
    return;
  }
  tbody.innerHTML = list
    .map((t) => {
      const diskon = t.diskon > 0 ? `<span class="cell-danger">- ${formatRupiah(t.diskon)}</span>` : "Rp 0";
      const waktu = new Date(t.waktu).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      return `
        <tr>
          <td class="cell-strong">${t.no_transaksi}</td>
          <td>${t.customer}</td>
          <td class="cell-muted">${t.produk}</td>
          <td class="cell-strong">${formatRupiah(t.total)}</td>
          <td>${diskon}</td>
          <td>${t.metode}</td>
          <td>${t.kasir}</td>
          <td class="cell-muted">${waktu}</td>
        </tr>
      `;
    })
    .join("");
}

function renderPagination(p) {
  document.getElementById("pagination-info").textContent =
    `Menampilkan ${Math.min(p.page * p.per_page, p.total)} dari ${p.total.toLocaleString("id-ID")} transaksi`;

  const el = document.getElementById("pagination");
  let html = `<button class="page-btn" id="page-prev" ${p.page <= 1 ? "disabled" : ""}><i data-lucide="chevron-left"></i></button>`;
  for (let i = 1; i <= p.total_pages; i++) {
    html += `<button class="page-btn ${i === p.page ? "active" : ""}" data-page="${i}">${i}</button>`;
  }
  html += `<button class="page-btn" id="page-next" ${p.page >= p.total_pages ? "disabled" : ""}><i data-lucide="chevron-right"></i></button>`;
  el.innerHTML = html;
  refreshIcons();

  el.querySelectorAll("[data-page]").forEach((btn) =>
    btn.addEventListener("click", () => {
      state.page = parseInt(btn.dataset.page);
      muatPenjualan();
    })
  );
  const prev = document.getElementById("page-prev");
  const next = document.getElementById("page-next");
  prev.addEventListener("click", () => {
    if (state.page > 1) { state.page -= 1; muatPenjualan(); }
  });
  next.addEventListener("click", () => {
    if (state.page < p.total_pages) { state.page += 1; muatPenjualan(); }
  });
}

// ----- Event listeners -----
document.querySelectorAll("#filter-tabs .filter-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#filter-tabs .filter-tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    state.range = tab.dataset.range;
    state.start = "";
    state.end = "";
    state.page = 1;
    muatPenjualan();
  });
});

document.getElementById("filter-start").addEventListener("change", (e) => {
  state.start = e.target.value;
  state.page = 1;
  muatPenjualan();
});
document.getElementById("filter-end").addEventListener("change", (e) => {
  state.end = e.target.value;
  state.page = 1;
  muatPenjualan();
});

document.getElementById("search-transaksi").addEventListener("input", (e) => {
  clearTimeout(timerSearch);
  const value = e.target.value;
  timerSearch = setTimeout(() => {
    state.search = value;
    state.page = 1;
    muatPenjualan();
  }, 300);
});

document.getElementById("btn-export").addEventListener("click", () => {
  const params = new URLSearchParams();
  params.set("range", state.range);
  if (state.start) params.set("start", state.start);
  if (state.end) params.set("end", state.end);
  if (state.search) params.set("search", state.search);
  window.location.href = `/api/penjualan/export?${params.toString()}`;
});

muatPenjualan();
