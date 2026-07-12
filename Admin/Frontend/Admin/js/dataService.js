const DataService = {
  async getProduk(){ const r = await Api.getProduk(); return r.produk; },
  async addProduk(data){ const r = await Api.addProduk(data); return r.produk; },
  async updateProduk(kode, patch){ const r = await Api.updateProduk(kode, patch); return r.produk; },
  async deleteProduk(kode){ return Api.deleteProduk(kode); },
  async adjustStok(kode, mode, jumlah){ const r = await Api.updateStok(kode, mode, jumlah); return r.produk; },
  async uploadFotoProduk(kode, file){ return Api.uploadFotoProduk(kode, file); },

  async getDiskon(){ const r = await Api.getDiskon(); return r.diskon; },
  async addDiskon(data){ const r = await Api.addDiskon(data); return r.diskon; },
  async updateDiskon(id, patch){ const r = await Api.updateDiskon(id, patch); return r.diskon; },
  async deleteDiskon(id){ return Api.deleteDiskon(id); },
  isDiskonBerlaku(d){
    if(d.status !== 'Aktif') return false;
    const today = dateOffset(0);
    return d.mulai <= today && today <= d.selesai;
  },

  async getTransaksi(start, end){ const r = await Api.getTransaksi(start, end); return r.transaksi; },
  async saveTransaksi(trx){ const r = await Api.saveTransaksi(trx); return r.transaksi; },

  async getLaporan(start, end){ return Api.getLaporan(start, end); },

  async getNotifikasi(){ return Api.getNotifikasi(); }, 
  async bacaNotifikasi(id){ return Api.bacaNotifikasi(id); },
  async bacaSemuaNotifikasi(){ return Api.bacaSemuaNotifikasi(); },

  async getProfil(){ const r = await Api.getProfil(); return r.profil; },
  async updateProfil(data){ const r = await Api.updateProfil(data); return r.profil; },
  async gantiPassword(lama, baru){ return Api.gantiPassword(lama, baru); },
  async uploadFotoProfil(file){ return Api.uploadFotoProfil(file); },
};
