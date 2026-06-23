/**
 * sidebar.js
 * Mengatur toggle sidebar di tampilan mobile (lebar <= 820px),
 * lihat tombol hamburger di partials/header_*.html
 */
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("sidebar-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
  });

  document.addEventListener("click", (e) => {
    if (
      sidebar.classList.contains("open") &&
      !sidebar.contains(e.target) &&
      !toggleBtn.contains(e.target)
    ) {
      sidebar.classList.remove("open");
    }
  });
});
