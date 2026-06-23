/**
 * tambah_produk.js
 * Logika halaman "Tambah Produk Baru":
 *  - klik dropzone -> buka file picker, tampilkan preview foto
 *  - toggle status Tersedia / Habis
 *  - submit form -> POST /api/produk (multipart, termasuk file foto)
 */

const inputFoto = document.getElementById("input-foto");
const dropzone = document.getElementById("dropzone");
const optTersedia = document.getElementById("opt-tersedia");
const optHabis = document.getElementById("opt-habis");

inputFoto.addEventListener("change", () => {
  const file = inputFoto.files[0];
  if (!file) return;

  if (file.size > 2 * 1024 * 1024) {
    toast("Ukuran foto maksimal 2MB", "error");
    inputFoto.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    dropzone.innerHTML = `<img class="preview" src="${e.target.result}" alt="Preview foto produk" />`;
  };
  reader.readAsDataURL(file);
});

function pilihStatus(value) {
  optTersedia.classList.toggle("selected-tersedia", value === "tersedia");
  optHabis.classList.toggle("selected-habis", value === "habis");
  document.querySelector(`input[name="status"][value="${value}"]`).checked = true;
}
optTersedia.addEventListener("click", () => pilihStatus("tersedia"));
optHabis.addEventListener("click", () => pilihStatus("habis"));

document.getElementById("form-produk").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);

  try {
    await apiFetch("/api/produk", { method: "POST", body: formData });
    toast("Produk berhasil disimpan");
    window.location.href = "/produk";
  } catch (err) {
    toast(err.message, "error");
  }
});
