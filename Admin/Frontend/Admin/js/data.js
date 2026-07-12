const KATEGORI_ICON = {
  'Kopi': '☕',
  'Non-Kopi': '🧋',
  'Makanan': '🥐',
  'Snack': '🍪',
};

function dateOffset(days){
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0,10);
}

function formatRupiah(n){
  return 'Rp' + Number(n||0).toLocaleString('id-ID');
}
function formatTanggal(iso){
  if(!iso) return '-';
  const d = new Date(String(iso).slice(0,10)+'T00:00:00');
  return d.toLocaleDateString('id-ID', { day:'2-digit', month:'short', year:'numeric' });
}
function formatWaktuNotif(iso){
  if(!iso) return '-';
  const d = new Date(iso);
  const diffMin = Math.floor((Date.now()-d.getTime())/60000);
  if(diffMin < 1) return 'Baru saja';
  if(diffMin < 60) return `${diffMin} menit lalu`;
  const diffJam = Math.floor(diffMin/60);
  if(diffJam < 24) return `${diffJam} jam lalu`;
  return formatTanggal(iso);
}
function initials(name){
  return (name||'?').split(' ').map(w=>w[0]).slice(0,2).join('').toUpperCase();
}
