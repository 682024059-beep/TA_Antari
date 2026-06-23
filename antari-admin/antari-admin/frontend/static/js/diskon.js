/**
 * diskon.js
 * Logika halaman "Manajemen Diskon": render tabel diskon, kartu statistik,
 * dan modal tambah diskon baru.
 */

async function muatDiskon() {
  const tbody = document.getElementById("diskon-tbody");
  try {
    const list = await apiFetch("/api/diskon");
    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Belum ada diskon. Klik "Tambah Diskon" untuk membuat promo baru.</td></tr>`;
      return;
    }
    tbody.innerHTML = list.map(rowDiskon).join("");
    refreshIcons();
    document.querySelectorAll("[data-hapus-diskon]").forEach((btn) => {
      btn.addEventListener("click", () => hapusDiskon(btn.dataset.hapusDiskon));
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Gagal memuat diskon: ${err.message}</td></tr>`;
  }
}

function rowDiskon(d) {
  const nilai = d.jenis === "Persentase" ? `${d.nilai}%` : formatRupiah(d.nilai);
  const badge = d.status === "AKTIF" ? `<span class="badge badge-aktif">AKTIF</span>` : `<span class="badge badge-draft">DRAFT</span>`;
  return `
    <tr>
      <td class="cell-strong">${d.nama}</td>
      <td class="cell-muted">${d.produk_target}</td>
      <td class="cell-muted">${d.jenis}</td>
      <td class="cell-danger">${nilai}</td>
      <td class="cell-muted">${d.periode_label}</td>
      <td>${badge}</td>
      <td>
        <button class="cell-action-btn" data-hapus-diskon="${d.id}" title="Hapus diskon">
          <i data-lucide="trash-2"></i>
        </button>
      </td>
    </tr>
  `;
}

async function muatStatsDiskon() {
  try {
    const s = await apiFetch("/api/diskon/stats");
    document.getElementById("stat-total-diskon").textContent = s.total_diskon_digunakan.toLocaleString("id-ID");
    const tandaPersen = s.perubahan_persen >= 0 ? "+" : "";
    document.getElementById("stat-perubahan-diskon").innerHTML =
      `<i data-lucide="trending-up"></i> ${tandaPersen}${s.perubahan_persen}% dari bulan lalu`;
    document.getElementById("stat-potongan-harga").textContent = formatRupiahSingkat(s.potongan_harga_berjalan);
    document.getElementById("stat-pencapaian-persen").textContent = `${s.pencapaian_persen}%`;
    document.getElementById("stat-progress-fill").style.width = `${s.pencapaian_persen}%`;
    refreshIcons();
  } catch (err) {
    toast(err.message, "error");
  }
}

async function hapusDiskon(id) {
  if (!confirm("Hapus diskon ini?")) return;
  try {
    await apiFetch(`/api/diskon/${id}`, { method: "DELETE" });
    toast("Diskon berhasil dihapus");
    muatDiskon();
    muatStatsDiskon();
  } catch (err) {
    toast(err.message, "error");
  }
}

// ----- Modal tambah diskon -----
const modal = document.getElementById("modal-diskon");
document.getElementById("btn-tambah-diskon").addEventListener("click", () => {
  modal.style.display = "flex";
});
document.getElementById("btn-batal-diskon").addEventListener("click", () => {
  modal.style.display = "none";
});
modal.addEventListener("click", (e) => {
  if (e.target === modal) modal.style.display = "none";
});

document.getElementById("form-diskon").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    await apiFetch("/api/diskon", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    toast("Diskon berhasil ditambahkan");
    modal.style.display = "none";
    form.reset();
    muatDiskon();
    muatStatsDiskon();
  } catch (err) {
    toast(err.message, "error");
  }
});

muatDiskon();
muatStatsDiskon();
