const NAV_ITEMS = {
  admin: [
    { key:'dashboard', label:'Dashboard', icon:'dashboard', href:'dashboard.html' },
    { key:'produk', label:'Manage Produk', icon:'box', href:'produk.html' },
    { key:'diskon', label:'Diskon', icon:'percent', href:'diskon.html' },
    { key:'riwayat', label:'Riwayat Transaksi', icon:'clock', href:'riwayat.html' },
    { key:'laporan', label:'Laporan Penjualan', icon:'chart', href:'laporan.html' },
    { key:'akun-kasir', label:'Akun Kasir', icon:'user', href:'akun-kasir.html' },
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
  'akun-kasir': ['Akun Kasir', 'Kelola akun kasir yang dapat login ke sistem POS'],
};

const USER_ICON = `
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M22 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
`;

const NOTIF_ICON = {
  stok_menipis: 'alert',
  stok_habis: 'alert',
  transaksi_baru: 'cart',
  produk_baru: 'box',
  produk_update: 'box',
  produk_hapus: 'box',
  diskon: 'percent',
  sistem: 'bell',
};

function getLayoutIcon(iconName){
  if(iconName === 'user'){
    return ICONS.user || USER_ICON;
  }

  return ICONS[iconName] || ICONS.bell || '';
}

function renderLayout(activeKey){
  const session = requireAuth(['admin']);
  const currentPath = window.location.pathname;

  const hideTopbarActions =
    activeKey === "akun-kasir" ||
    activeKey === "profil" ||
    currentPath.includes("/admin/akun-kasir.html") ||
    currentPath.includes("/admin/profil.html");

  document.body.classList.toggle("hide-topbar-actions", hideTopbarActions);

  if(!session){
    return null;
  }

  document.body.classList.remove('page-ready');
  document.body.classList.remove('page-leaving');

  const role = session.role || 'admin';
  const items = NAV_ITEMS[role] || NAV_ITEMS.admin;

  const sidebarEl =
    document.getElementById('sidebar-placeholder') ||
    document.getElementById('sidebar');

  const topbarEl =
    document.getElementById('topbar-placeholder') ||
    document.getElementById('topbar');

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
            <a class="nav-item ${it.key === activeKey ? 'active' : ''}" href="${it.href}">
              ${getLayoutIcon(it.icon)}
              <span>${it.label}</span>
            </a>
          `).join('')}
        </nav>

        <div class="sidebar__footer">
          <a class="user-card" id="sidebar-profile-link" href="profil.html" style="text-decoration:none; color:inherit; cursor:pointer;">
            <div class="avatar" id="sidebar-avatar">${initials(session.nama)}</div>
            <div class="who">
              <div class="name">${session.nama}</div>
              <div class="role">${role === 'admin' ? 'Admin' : 'Kasir'}</div>
            </div>
          </a>

          <button class="logout-btn" id="btn-logout">
            ${ICONS.logout}
            <span>Keluar</span>
          </button>
        </div>
      </aside>
    `;

    const sidebarAvatar = document.getElementById('sidebar-avatar');

    if(session.foto_url && sidebarAvatar){
      sidebarAvatar.innerHTML = `
        <img
          src="${session.foto_url}"
          alt="${session.nama}"
          style="width:100%;height:100%;object-fit:cover;border-radius:inherit;"
        >
      `;
    }

    const logoutBtn = document.getElementById('btn-logout');

    if(logoutBtn){
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();

        if(typeof openConfirm === 'function'){
          openConfirm(
            'Keluar dari sistem?',
            'Anda perlu login kembali untuk mengakses ANTARI.',
            logout
          );
        }else{
          if(confirm('Keluar dari sistem?')){
            logout();
          }
        }
      });
    }
  }

  if(topbarEl){
    const [title, crumb] = PAGE_TITLES[activeKey] || ['ANTARI', ''];

    const currentPath = window.location.pathname;

const hideSearchAndNotif =
  currentPath.includes("/admin/akun-kasir.html") ||
  currentPath.includes("/admin/profil.html") ||
  activeKey === "akun-kasir" ||
  activeKey === "profil";

    topbarEl.outerHTML = `
      <header class="topbar" id="topbar">
        <div class="topbar__title">
          <h1>${title}</h1>
          <div class="crumb">${crumb}</div>
        </div>

        ${activeKey !== 'dashboard' ? `
  <div
  class="topbar__search"
  id="global-search-wrap"
  style="${hideTopbarTools ? 'display:none !important;' : ''}"
>
    ${ICONS.search}
    <input type="text" id="global-search" placeholder="Cari produk, transaksi..." />
  </div>
` : ''}

          <div style="position:relative; ${hideTopbarTools ? 'display:none !important;' : ''}">
            <button class="icon-btn" id="btn-notif" title="Notifikasi">
              ${ICONS.bell}
              <span class="dot" id="notif-dot" style="display:none;"></span>
            </button>
            <div class="notif-dropdown" id="notif-dropdown"></div>
          </div>

          <a href="profil.html" class="topbar__avatar" id="topbar-avatar" title="${session.nama}">
            ${initials(session.nama)}
          </a>
        </div>
      </header>
    `;

    const topbarAvatar = document.getElementById('topbar-avatar');

    if(session.foto_url && topbarAvatar){
      topbarAvatar.innerHTML = `
        <img
          src="${session.foto_url}"
          alt="${session.nama}"
          style="width:100%;height:100%;object-fit:cover;border-radius:inherit;"
        >
      `;
    }

    setupNotifBell();
  }

  requestAnimationFrame(() => {
    document.body.classList.add('page-ready');
  });

  return session;
}

function setupNotifBell(){
  const btn = document.getElementById('btn-notif');
  const dropdown = document.getElementById('notif-dropdown');
  const dot = document.getElementById('notif-dot');

  if(!btn || !dropdown){
    return;
  }

  ensureNotifStyles();

  async function refreshBadge(){
    try{
      const { notifikasi, unread } = await DataService.getNotifikasi();

      if(dot){
        dot.style.display = unread > 0 ? 'block' : 'none';
      }

      renderNotifList(notifikasi || []);
    }catch(err){
      renderNotifList([], true);

      if(dot){
        dot.style.display = 'none';
      }
    }
  }

  function renderNotifList(list, isError){
    if(isError){
      dropdown.innerHTML = `
        <div class="notif-empty">
          Gagal memuat notifikasi. Periksa koneksi ke server.
        </div>
      `;
      return;
    }

    if(!list.length){
      dropdown.innerHTML = `
        <div class="notif-empty">
          ${ICONS.inbox}
          <div>Belum ada notifikasi.</div>
        </div>
      `;
      return;
    }

    dropdown.innerHTML = `
      <div class="notif-head">
        <span>Notifikasi</span>
        <button type="button" id="notif-mark-all">Tandai semua dibaca</button>
      </div>

      <div class="notif-list">
        ${list.map(n => `
          <div class="notif-item ${n.is_read ? '' : 'unread'}" data-id="${n.id}">
            <div class="notif-item__icon">
              ${ICONS[NOTIF_ICON[n.tipe] || 'bell']}
            </div>

            <div class="notif-item__body">
              <div class="notif-item__title">${n.judul || 'Notifikasi'}</div>
              <div class="notif-item__msg">${n.pesan || ''}</div>
              <div class="notif-item__time">${formatWaktuNotif(n.created_at)}</div>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    const markAllBtn = document.getElementById('notif-mark-all');

    if(markAllBtn){
      markAllBtn.addEventListener('click', async (e) => {
        e.stopPropagation();

        try{
          await DataService.bacaSemuaNotifikasi();

          if(dot){
            dot.style.display = 'none';
          }

          refreshBadge();
        }catch(err){
          if(typeof showToast === 'function'){
            showToast('Gagal menandai notifikasi.', 'danger');
          }
        }
      });
    }

    dropdown.querySelectorAll('.notif-item').forEach(el => {
      el.addEventListener('click', async () => {
        try{
          await DataService.bacaNotifikasi(el.dataset.id);
          el.classList.remove('unread');
          refreshBadge();
        }catch(err){
          if(typeof showToast === 'function'){
            showToast('Gagal membaca notifikasi.', 'danger');
          }
        }
      });
    });
  }

  btn.addEventListener('click', async (e) => {
    e.stopPropagation();

    const isOpen = dropdown.classList.toggle('open');

    if(isOpen){
      await refreshBadge();
    }
  });

  document.addEventListener('click', (e) => {
    if(!dropdown.contains(e.target) && !btn.contains(e.target)){
      dropdown.classList.remove('open');
    }
  });

  refreshBadge();

  if(window.__notifPollingTimer){
    clearInterval(window.__notifPollingTimer);
  }

  window.__notifPollingTimer = setInterval(refreshBadge, 60000);
}

function ensureNotifStyles(){
  if(document.getElementById('notif-dropdown-style')){
    return;
  }

  const style = document.createElement('style');
  style.id = 'notif-dropdown-style';

  style.textContent = `
    .notif-dropdown{
      position:absolute;
      right:0;
      top:calc(100% + 10px);
      width:340px;
      max-height:420px;
      background:#fff;
      border:1px solid #e5ddd3;
      border-radius:14px;
      box-shadow:0 12px 32px rgba(43,33,24,.14);
      display:none;
      overflow:hidden;
      z-index:60;
    }

    .notif-dropdown.open{
      display:flex;
      flex-direction:column;
    }

    .notif-head{
      display:flex;
      justify-content:space-between;
      align-items:center;
      padding:12px 14px;
      border-bottom:1px solid #f0e9df;
      font-weight:600;
      font-size:13.5px;
    }

    .notif-head button{
      background:none;
      border:none;
      color:#a9713f;
      font-size:12px;
      cursor:pointer;
      font-weight:600;
    }

    .notif-list{
      overflow-y:auto;
      max-height:360px;
    }

    .notif-empty{
      padding:28px 16px;
      text-align:center;
      color:#9c8c7d;
      font-size:13px;
      display:flex;
      flex-direction:column;
      align-items:center;
      gap:8px;
    }

    .notif-empty svg{
      width:42px;
      height:42px;
      opacity:.65;
    }

    .notif-item{
      display:flex;
      gap:10px;
      padding:12px 14px;
      border-bottom:1px solid #f6f1ea;
      cursor:pointer;
    }

    .notif-item:hover{
      background:#faf6f0;
    }

    .notif-item.unread{
      background:#fdf6ec;
    }

    .notif-item__icon{
      width:32px;
      height:32px;
      flex:none;
      border-radius:9px;
      background:#f3e9dc;
      color:#a9713f;
      display:flex;
      align-items:center;
      justify-content:center;
    }

    .notif-item__icon svg{
      width:16px;
      height:16px;
    }

    .notif-item__title{
      font-size:13px;
      font-weight:600;
      color:#2b2118;
    }

    .notif-item__msg{
      font-size:12.5px;
      color:#7a6a5c;
      margin-top:2px;
      line-height:1.4;
    }

    .notif-item__time{
      font-size:11px;
      color:#b3a494;
      margin-top:4px;
    }
  `;

  document.head.appendChild(style);
}


function parseAntariDate(value){
  if(!value) return null;

  let s = String(value).trim();

  if(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(s)){
    s = s.replace(' ', 'T') + 'Z';
  }

  if(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(s)){
    s = s + 'Z';
  }

  return new Date(s);
}

function formatWaktuNotif(value){
  const date = parseAntariDate(value);

  if(!date || isNaN(date.getTime())){
    return '';
  }

  let diffMs = Date.now() - date.getTime();

  if(diffMs < 0){
    diffMs = 0;
  }

  const detik = Math.floor(diffMs / 1000);
  const menit = Math.floor(detik / 60);
  const jam = Math.floor(menit / 60);
  const hari = Math.floor(jam / 24);

  if(detik < 60){
    return 'baru saja';
  }

  if(menit < 60){
    return `${menit} menit lalu`;
  }

  if(jam < 24){
    return `${jam} jam lalu`;
  }

  if(hari === 1){
    return 'kemarin';
  }

  return date.toLocaleDateString('id-ID', {
    day:'2-digit',
    month:'short',
    year:'numeric'
  });
}

function enableSmoothNavigation(){
  return;
}


function isProtectedAdminPage(){
  const path = window.location.pathname;

  if(!path.startsWith("/admin/")){
    return false;
  }

  const publicPages = [
    "/admin/login.html",
    "/admin/forgot-password.html",
    "/admin/reset-password.html"
  ];

  return !publicPages.includes(path);
}

function forceAdminLogoutRedirect(){
  try{
    localStorage.clear();
    sessionStorage.clear();
  }catch(err){}

  window.location.replace("/admin/login.html");
}

function validateAdminSessionOnBack(){
  if(!isProtectedAdminPage()){
    return;
  }

  let session = null;

  try{
    if(typeof requireAuth === "function"){
      session = requireAuth(["admin"]);
    }
  }catch(err){
    session = null;
  }

  if(!session || session.role !== "admin"){
    forceAdminLogoutRedirect();
  }
}

window.addEventListener("pageshow", function(event){
  const navEntry = performance.getEntriesByType("navigation")[0];
  const isBackForward = event.persisted || (navEntry && navEntry.type === "back_forward");

  if(isBackForward){
    validateAdminSessionOnBack();
  }
});

document.addEventListener("visibilitychange", function(){
  if(document.visibilityState === "visible"){
    validateAdminSessionOnBack();
  }
});