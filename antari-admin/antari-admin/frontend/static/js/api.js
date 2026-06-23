/**
 * api.js
 * Kumpulan fungsi bantu yang dipakai di semua halaman:
 *  - apiFetch(): wrapper fetch() dengan penanganan error JSON yang konsisten
 *  - formatRupiah(): format angka jadi "Rp 25.000"
 *  - formatRupiahSingkat(): format ringkas seperti di kartu statistik, "Rp 4.2M"
 *  - refreshIcons(): re-render ikon lucide setelah HTML baru disisipkan lewat JS
 *  - toast(): notifikasi kecil di pojok layar untuk sukses/gagal aksi
 */

async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  let body = null;
  try {
    body = await res.json();
  } catch (err) {
    body = null;
  }
  if (!res.ok) {
    const message = (body && body.error) || `Permintaan gagal (${res.status})`;
    throw new Error(message);
  }
  return body;
}

function formatRupiah(angka) {
  return "Rp " + Math.round(angka || 0).toLocaleString("id-ID");
}

function formatRupiahSingkat(angka) {
  const n = Number(angka) || 0;
  if (n >= 1_000_000_000) return "Rp " + (n / 1_000_000_000).toFixed(1) + "B";
  if (n >= 1_000_000) return "Rp " + (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return "Rp " + (n / 1_000).toFixed(1) + "K";
  return formatRupiah(n);
}

function formatTanggalSingkat(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleDateString("id-ID", { day: "2-digit", month: "short" });
}

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons();
}

function toast(message, type = "success") {
  let box = document.getElementById("toast-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "toast-box";
    box.style.position = "fixed";
    box.style.bottom = "24px";
    box.style.right = "24px";
    box.style.zIndex = "1000";
    box.style.display = "flex";
    box.style.flexDirection = "column";
    box.style.gap = "8px";
    document.body.appendChild(box);
  }
  const item = document.createElement("div");
  item.textContent = message;
  item.style.padding = "12px 18px";
  item.style.borderRadius = "8px";
  item.style.fontSize = "14px";
  item.style.fontWeight = "600";
  item.style.color = "#fff";
  item.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
  item.style.background = type === "success" ? "#1f9d55" : "#c0392b";
  box.appendChild(item);
  setTimeout(() => item.remove(), 3000);
}
