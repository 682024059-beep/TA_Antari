/* ============================================================
   ANTARI — Layout renderer (sidebar + topbar)
   Notifikasi (lonceng) & Profil sekarang benar-benar terhubung
   ke backend (bukan lagi ikon statis / dekorasi).
   ============================================================ */

const NAV_ITEMS = {
  admin: [
    { key:'dashboard', label:'Dashboard', icon:'dashboard', href:'dashboard.html' },
    { key:'produk', label:'Manage Produk', icon:'box', href:'produk.html' },
    { key:'diskon', label:'Diskon', icon:'percent', href:'diskon.html' },
    { key:'riwayat', label:'Riwayat Transaksi', icon:'clock', href:'riwayat.html' },
    { key:'laporan', label:'Laporan Penjualan', icon:'chart', href:'laporan.html' },
  ],
};

const PAGE_TITLES = {
  dashboard: ['Dashboard', 'Ringkasan aktivitas CoffeeShop Antari hari ini'],
  produk: ['Manage Produk', 'Kelola menu, harga, kategori, dan stok produk dalam satu halaman'],
  diskon: ['Pengelolaan Diskon', 'Atur program diskon yang sedang berjalan'],
  riwayat: ['Riwayat Transaksi', 'Daftar seluruh transaksi yang telah tercatat'],
  laporan: ['Laporan Penjualan', 'Evaluasi performa penjualan berdasarkan periode'],
  transaksi: ['Transaksi Penjualan', 'Catat pesanan dan proses pembayaran pelanggan'],
  profil: ['Profil Saya', 'Kelola informasi akun dan keamanan login Anda'],
};

const NOTIF_ICON = {
  stok_menipis: 'alert', stok_habis: 'alert', transaksi_baru: 'cart', diskon: 'percent', sistem: 'bell',
};

function renderLayout(activeKey){
  const session = requireAuth(['admin']);
  if(!session) return null;
  const role = session.role;
  const items = NAV_ITEMS[role] || [];
  const root = rootPath();

  const sidebarEl = document.getElementById('sidebar-placeholder');
  const topbarEl = document.getElementById('topbar-placeholder');

  if(sidebarEl){
    sidebarEl.outerHTML = `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar__brand">
        <div class="mark">${ICONS.cup}</div>
        <div>
          <div class="word">ANTARI</div>
          <div class="sub">${role === 'admin' ? 'Sistem Manajemen' : 'Sistem POS'}</div>
        </div>
      </div>
      <nav class="sidebar__nav">
        <div class="sidebar__section-label">Menu</div>
        ${items.map(it => `
          <a class="nav-item ${it.key===activeKey?'active':''}" href="${it.href}">
            ${ICONS[it.icon]}<span>${it.label}</span>
          </a>`).join('')}
      </nav>
      <div class="sidebar__footer">
        <a class="user-card" id="sidebar-profile-link" href="profil.html" style="text-decoration:none; color:inherit; cursor:pointer;">
          <div class="avatar" id="sidebar-avatar">${initials(session.nama)}</div>
          <div class="who">
            <div class="name">${session.nama}</div>
            <div class="role">${role === 'admin' ? 'Admin' : 'Kasir'}</div>
          </div>
        </a>
        <button class="logout-btn" id="btn-logout">${ICONS.logout}<span>Keluar</span></button>
      </div>
    </aside>`;
    if(session.foto_url){
      document.getElementById('sidebar-avatar').innerHTML = `<img src="${session.foto_url}" alt="${session.nama}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;">`;
    }
    document.getElementById('btn-logout').addEventListener('click', (e) => {
      e.preventDefault();
      openConfirm('Keluar dari sistem?', 'Anda perlu login kembali untuk mengakses ANTARI.', logout);
    });
  }

  if(topbarEl){
    const [title, crumb] = PAGE_TITLES[activeKey] || ['ANTARI', ''];
    topbarEl.outerHTML = `
    <header class="topbar" id="topbar">
      <div class="topbar__title">
        <h1>${title}</h1>
        <div class="crumb">${crumb}</div>
      </div>
      <div class="topbar__right">
        <div class="topbar__search" id="global-search-wrap">
          ${ICONS.search}
          <input type="text" id="global-search" placeholder="Cari produk, transaksi..." />
        </div>
        <div style="position:relative;">
          <button class="icon-btn" id="btn-notif" title="Notifikasi">${ICONS.bell}<span class="dot" id="notif-dot" style="display:none;"></span></button>
          <div class="notif-dropdown" id="notif-dropdown"></div>
        </div>
        <a href="profil.html" class="topbar__avatar" id="topbar-avatar" title="${session.nama}">${initials(session.nama)}</a>
      </div>
    </header>`;
    if(session.foto_url){
      document.getElementById('topbar-avatar').innerHTML = `<img src="${session.foto_url}" alt="${session.nama}" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;">`;
    }
    setupNotifBell();
  }

  return session;
}

/* ---------------- Notifikasi (lonceng) ---------------- */
function setupNotifBell(){
  const btn = document.getElementById('btn-notif');
  const dropdown = document.getElementById('notif-dropdown');
  if(!btn || !dropdown) return;

  ensureNotifStyles();

  async function refreshBadge(){
    try{
      const { notifikasi, unread } = await DataService.getNotifikasi();
      document.getElementById('notif-dot').style.display = unread > 0 ? 'block' : 'none';
      renderNotifList(notifikasi);
    }catch(err){
      renderNotifList([], true);
    }
  }

  function renderNotifList(list, isError){
    if(isError){
      dropdown.innerHTML = `<div class="notif-empty">Gagal memuat notifikasi. Periksa koneksi ke server.</div>`;
      return;
    }
    if(!list.length){
      dropdown.innerHTML = `<div class="notif-empty">${ICONS.inbox}<div>Belum ada notifikasi.</div></div>`;
      return;
    }
    dropdown.innerHTML = `
      <div class="notif-head">
        <span>Notifikasi</span>
        <button id="notif-mark-all">Tandai semua dibaca</button>
      </div>
      <div class="notif-list">
        ${list.map(n => `
          <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
            <div class="notif-item__icon">${ICONS[NOTIF_ICON[n.tipe]||'bell']}</div>
            <div class="notif-item__body">
              <div class="notif-item__title">${n.judul}</div>
              <div class="notif-item__msg">${n.pesan}</div>
              <div class="notif-item__time">${formatWaktuNotif(n.created_at)}</div>
            </div>
          </div>
        `).join('')}
      </div>`;
    const markAllBtn = document.getElementById('notif-mark-all');
    if(markAllBtn) markAllBtn.addEventListener('click', async () => {
      await DataService.bacaSemuaNotifikasi();
      refreshBadge();
    });
    dropdown.querySelectorAll('.notif-item').forEach(el => {
      el.addEventListener('click', async () => {
        await DataService.bacaNotifikasi(el.dataset.id);
        el.classList.remove('unread');
        refreshBadge();
      });
    });
  }

  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const isOpen = dropdown.classList.toggle('open');
    if(isOpen) refreshBadge();
  });
  document.addEventListener('click', (e) => {
    if(!dropdown.contains(e.target) && e.target !== btn) dropdown.classList.remove('open');
  });

  refreshBadge();
  setInterval(refreshBadge, 60000); // polling ringan tiap 1 menit
}

function ensureNotifStyles(){
  if(document.getElementById('notif-dropdown-style')) return;
  const style = document.createElement('style');
  style.id = 'notif-dropdown-style';
  style.textContent = `
    .notif-dropdown{ position:absolute; right:0; top:calc(100% + 10px); width:340px; max-height:420px;
      background:#fff; border:1px solid #e5ddd3; border-radius:14px; box-shadow:0 12px 32px rgba(43,33,24,.14);
      display:none; overflow:hidden; z-index:60; }
    .notif-dropdown.open{ display:flex; flex-direction:column; }
    .notif-head{ display:flex; justify-content:space-between; align-items:center; padding:12px 14px;
      border-bottom:1px solid #f0e9df; font-weight:600; font-size:13.5px; }
    .notif-head button{ background:none; border:none; color:#a9713f; font-size:12px; cursor:pointer; font-weight:600; }
    .notif-list{ overflow-y:auto; max-height:360px; }
    .notif-empty{ padding:28px 16px; text-align:center; color:#9c8c7d; font-size:13px; display:flex; flex-direction:column; align-items:center; gap:8px;}
    .notif-item{ display:flex; gap:10px; padding:12px 14px; border-bottom:1px solid #f6f1ea; cursor:pointer; }
    .notif-item:hover{ background:#faf6f0; }
    .notif-item.unread{ background:#fdf6ec; }
    .notif-item__icon{ width:32px; height:32px; flex:none; border-radius:9px; background:#f3e9dc; color:#a9713f;
      display:flex; align-items:center; justify-content:center; }
    .notif-item__icon svg{ width:16px; height:16px; }
    .notif-item__title{ font-size:13px; font-weight:600; color:#2b2118; }
    .notif-item__msg{ font-size:12.5px; color:#7a6a5c; margin-top:2px; line-height:1.4; }
    .notif-item__time{ font-size:11px; color:#b3a494; margin-top:4px; }
  `;
  document.head.appendChild(style);
}
