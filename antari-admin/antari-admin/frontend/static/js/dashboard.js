/**
 * dashboard.js
 * Mengisi kartu statistik & grafik di halaman Dashboard, menggunakan
 * endpoint yang sama dengan halaman Riwayat Penjualan (/api/penjualan)
 * dengan rentang "bulanan" (bulan ini).
 */

let dashboardChart = null;

async function muatDashboard() {
  try {
    const data = await apiFetch("/api/penjualan?range=bulanan&per_page=1");
    renderStatCards(data.ringkasan);
    renderChart(data.grafik);
  } catch (err) {
    toast(err.message, "error");
  }
}

function renderStatCards(r) {
  const el = document.getElementById("dashboard-stats");
  const naik = (v) => (v >= 0 ? "+" : "") + v + "% vs bulan lalu";
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
    </div>
    <div class="card stat-card">
      <div class="stat-icon tone-blue"><i data-lucide="credit-card"></i></div>
      <div class="card-eyebrow">Metode Cashless</div>
      <div class="card-value">${formatRupiahSingkat(r.metode_cashless)}</div>
    </div>
  `;
  refreshIcons();
}

function renderChart(grafik) {
  const ctx = document.getElementById("dashboard-chart");
  if (dashboardChart) dashboardChart.destroy();
  dashboardChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: grafik.labels,
      datasets: [
        {
          label: "Pendapatan",
          data: grafik.values,
          backgroundColor: "#8b2e22",
          borderRadius: 6,
          maxBarThickness: 28,
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

muatDashboard();
