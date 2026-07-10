/* ============================================================
   ANTARI — Auth & Session
   F001 Login Sistem, F011 Logout Sistem

   Login memverifikasi ke backend lewat Api.login().
   Sesi disimpan sebagai JWT di localStorage, dan info tampilan
   disimpan di sessionStorage.
   ============================================================ */

const SESSION_KEY = 'antari_session_v1';

async function login(email, password){
  try{
    const res = await Api.login(email, password);

    setToken(res.token);

    const session = {
      id: res.user.id,
      username: res.user.username,
      nama: res.user.nama,
      role: res.user.role,
      email: res.user.email,
      foto_url: res.user.foto_url,
      loginAt: Date.now()
    };

    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));

    return {
      ok: true,
      session
    };
  }catch(err){
    return {
      ok: false,
      message: err.message || 'Email atau password salah. Silakan periksa kembali.'
    };
  }
}

function getSession(){
  const raw = sessionStorage.getItem(SESSION_KEY);

  if(!raw){
    return null;
  }

  try{
    return JSON.parse(raw);
  }catch(e){
    return null;
  }
}

function updateSessionCache(patch){
  const session = getSession();

  if(!session){
    return;
  }

  const merged = {
    ...session,
    ...patch
  };

  sessionStorage.setItem(SESSION_KEY, JSON.stringify(merged));
}

function logout(){
  clearToken();
  sessionStorage.removeItem(SESSION_KEY);
  window.location.href = rootPath() + 'login.html';
}

/* 
   Dipanggil di setiap halaman yang butuh login.
   Kalau belum login atau role tidak sesuai, user diarahkan ke login.
*/
function requireAuth(allowedRoles){
  const session = getSession();
  const token = getToken();

  if(!session || !token){
    window.location.href = rootPath() + 'login.html';
    return null;
  }

  if(allowedRoles && !allowedRoles.includes(session.role)){
    clearToken();
    sessionStorage.removeItem(SESSION_KEY);
    window.location.href = rootPath() + 'login.html';
    return null;
  }

  return session;
}