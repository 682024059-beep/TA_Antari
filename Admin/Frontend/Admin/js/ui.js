/* ============================================================
   ANTARI — UI helpers: toast & confirm dialog
   ============================================================ */

function ensureToastStack(){
  let stack = document.querySelector('.toast-stack');
  if(!stack){
    stack = document.createElement('div');
    stack.className = 'toast-stack';
    document.body.appendChild(stack);
  }
  return stack;
}

function showToast(message, type=''){
  const stack = ensureToastStack();
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(()=>{
    el.style.opacity = '0';
    el.style.transform = 'translateY(-6px)';
    el.style.transition = 'all .2s ease';
    setTimeout(()=>el.remove(), 220);
  }, 2600);
}

function ensureConfirmModal(){
  let overlay = document.getElementById('confirm-overlay');
  if(overlay) return overlay;
  overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'confirm-overlay';
  overlay.innerHTML = `
    <div class="modal">
      <div class="modal__header">
        <h3 id="confirm-title">Konfirmasi</h3>
        <button class="modal__close" id="confirm-close">${ICONS.close}</button>
      </div>
      <div class="modal__body">
        <p id="confirm-message" class="text-muted" style="font-size:13.5px; line-height:1.6;"></p>
      </div>
      <div class="modal__footer">
        <button class="btn btn-secondary" id="confirm-cancel">Batal</button>
        <button class="btn btn-danger" id="confirm-ok">Ya, Lanjutkan</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e)=>{ if(e.target === overlay) closeConfirm(); });
  document.getElementById('confirm-close').addEventListener('click', closeConfirm);
  document.getElementById('confirm-cancel').addEventListener('click', closeConfirm);
  return overlay;
}

function closeConfirm(){
  const overlay = document.getElementById('confirm-overlay');
  if(overlay) overlay.classList.remove('open');
}

function openConfirm(title, message, onConfirm, okLabel='Ya, Lanjutkan'){
  const overlay = ensureConfirmModal();
  document.getElementById('confirm-title').textContent = title;
  document.getElementById('confirm-message').textContent = message;
  const okBtn = document.getElementById('confirm-ok');
  okBtn.textContent = okLabel;
  const newOk = okBtn.cloneNode(true);
  okBtn.parentNode.replaceChild(newOk, okBtn);
  newOk.addEventListener('click', ()=>{ closeConfirm(); onConfirm(); });
  overlay.classList.add('open');
}

function openModal(id){ document.getElementById(id).classList.add('open'); }
function closeModal(id){ document.getElementById(id).classList.remove('open'); }
