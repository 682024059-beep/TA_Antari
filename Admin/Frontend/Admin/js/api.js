/* ============================================================
   ANTARI — API client
   Semua request ke backend (TiDB/Cloudinary/Resend) lewat sini.
   Ganti API_BASE_URL sesuai alamat server backend Anda.
   ============================================================ */

const API_BASE_URL = window.ANTARI_API_BASE_URL || '/api';
const TOKEN_KEY = 'antari_token_v1';

function rootPath(){
  return '/admin/';
}

function getToken(){
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(t){
  localStorage.setItem(TOKEN_KEY, t);
}

function clearToken(){
  localStorage.removeItem(TOKEN_KEY);
}

async function apiRequest(path, { method='GET', body, isForm=false } = {}){
  const headers = {};
  const token = getToken();

  if(token){
    headers['Authorization'] = 'Bearer ' + token;
  }

  if(!isForm){
    headers['Content-Type'] = 'application/json';
  }

  let res;

  try{
    res = await fetch(API_BASE_URL + path, {
      method,
      headers,
      body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
    });
  }catch(err){
    throw new Error('Tidak dapat terhubung ke server. Periksa koneksi atau alamat backend.');
  }

  let data = null;

  try{
    data = await res.json();
  }catch(e){
    // Respons kosong
  }

  if(res.status === 401){
    clearToken();
    sessionStorage.removeItem('antari_session_v1');

    if(!window.location.pathname.endsWith('login.html') && window.location.pathname !== '/'){
      window.location.href = rootPath() + 'login.html';
    }
  }

  if(!res.ok){
    throw new Error((data && data.message) || 'Terjadi kesalahan pada server.');
  }

  return data;
}

const Api = {
  // Auth
  login: (email, password) =>
    apiRequest('/auth/login', {
      method:'POST',
      body:{ email, password }
    }),

  forgotPassword: (email) =>
    apiRequest('/auth/forgot-password', {
      method:'POST',
      body:{ email }
    }),

  resetPassword: (token, password) =>
    apiRequest('/auth/reset-password', {
      method:'POST',
      body:{ token, password }
    }),

  me: () => apiRequest('/auth/me'),

  // Profil
  getProfil: () => apiRequest('/profil'),

  updateProfil: (data) =>
    apiRequest('/profil', {
      method:'PUT',
      body:data
    }),

  gantiPassword: (passwordLama, passwordBaru) =>
    apiRequest('/profil/ganti-password', {
      method:'POST',
      body:{ passwordLama, passwordBaru }
    }),

  uploadFotoProfil: (file) => {
    const fd = new FormData();
    fd.append('foto', file);

    return apiRequest('/profil/foto', {
      method:'POST',
      body:fd,
      isForm:true
    });
  },

  // Produk
  getProduk: () => apiRequest('/produk'),

  addProduk: (data) =>
    apiRequest('/produk', {
      method:'POST',
      body:data
    }),

  updateProduk: (kode, data) =>
    apiRequest('/produk/' + kode, {
      method:'PUT',
      body:data
    }),

  deleteProduk: (kode) =>
    apiRequest('/produk/' + kode, {
      method:'DELETE'
    }),

  updateStok: (kode, mode, jumlah) =>
    apiRequest(`/produk/${kode}/stok`, {
      method:'POST',
      body:{ mode, jumlah }
    }),

  uploadFotoProduk: (kode, file) => {
    const fd = new FormData();
    fd.append('foto', file);

    return apiRequest(`/produk/${kode}/foto`, {
      method:'POST',
      body:fd,
      isForm:true
    });
  },

  // Diskon
  getDiskon: () => apiRequest('/diskon'),

  addDiskon: (data) =>
    apiRequest('/diskon', {
      method:'POST',
      body:data
    }),

  updateDiskon: (id, data) =>
    apiRequest('/diskon/' + id, {
      method:'PUT',
      body:data
    }),

  deleteDiskon: (id) =>
    apiRequest('/diskon/' + id, {
      method:'DELETE'
    }),

  // Transaksi
  getTransaksi: (start, end) => {
    const qs = new URLSearchParams();

    if(start){
      qs.set('start', start);
    }

    if(end){
      qs.set('end', end);
    }

    const q = qs.toString();

    return apiRequest('/transaksi' + (q ? '?' + q : ''));
  },

  saveTransaksi: (data) =>
    apiRequest('/transaksi', {
      method:'POST',
      body:data
    }),

  // Laporan
  getLaporan: (start, end) => {
    const qs = new URLSearchParams();

    if(start){
      qs.set('start', start);
    }

    if(end){
      qs.set('end', end);
    }

    const q = qs.toString();

    return apiRequest('/laporan' + (q ? '?' + q : ''));
  },

  // Notifikasi
  getNotifikasi: () => apiRequest('/notifikasi'),

  bacaNotifikasi: (id) =>
    apiRequest(`/notifikasi/${id}/baca`, {
      method:'POST'
    }),

  bacaSemuaNotifikasi: () =>
    apiRequest('/notifikasi/baca-semua', {
      method:'POST'
    }),
};