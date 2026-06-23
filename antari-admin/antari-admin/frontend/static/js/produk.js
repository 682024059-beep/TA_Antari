/**
 * produk.js
 * Logika halaman "Manage Produk": ambil daftar produk dari API,
 * render ke tabel, fitur cari, dan hapus produk.
 */

let timerSearch = null;

async function muatProduk(search = "") {
  const tbody = document.getElementById("produk-tbody");
  try {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    const list = await apiFetch(`/api/produk?${params.toString()}`);

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Belum ada produk. Klik "Tambah Produk" untuk menambahkan.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(rowProduk).join("");
    refreshIcons();
    document.querySelectorAll("[data-hapus-produk]").forEach((btn) => {
      btn.addEventListener("click", () => hapusProduk(btn.dataset.hapusProduk, search));
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">Gagal memuat produk: ${err.message}</td></tr>`;
  }
}

function rowProduk(p) {
  const foto = p.foto
    ? `<img src="/static/${p.foto}" style="width:36px;height:36px;border-radius:8px;object-fit:cover;margin-right:10px;" />`
    : `<span style="display:inline-flex;width:36px;height:36px;border-radius:8px;background:#f3f0ed;margin-right:10px;align-items:center;justify-content:center;color:#b8aca4;"><i data-lucide="image"></i></span>`;
  const badge =
    p.status === "tersedia"
      ? `<span class="badge badge-aktif">TERSEDIA</span>`
      : `<span class="badge badge-habis">HABIS</span>`;

  return `
    <tr>
      <td class="cell-muted">${p.kode}</td>
      <td>
        <div style="display:flex;align-items:center;">
          ${foto}
          <span class="cell-strong">${p.nama}</span>
        </div>
      </td>
      <td class="cell-muted">${p.kategori || "-"}</td>
      <td class="cell-strong">${formatRupiah(p.harga)}</td>
      <td>${p.stok}</td>
      <td>${badge}</td>
      <td>
        <button class="cell-action-btn" data-hapus-produk="${p.id}" title="Hapus produk">
          <i data-lucide="trash-2"></i>
        </button>
      </td>
    </tr>
  `;
}

async function hapusProduk(id, search) {
  if (!confirm("Hapus produk ini?")) return;
  try {
    await apiFetch(`/api/produk/${id}`, { method: "DELETE" });
    toast("Produk berhasil dihapus");
    muatProduk(search);
  } catch (err) {
    toast(err.message, "error");
  }
}

document.getElementById("search-produk").addEventListener("input", (e) => {
  clearTimeout(timerSearch);
  const value = e.target.value;
  timerSearch = setTimeout(() => muatProduk(value), 300);
});

muatProduk();
