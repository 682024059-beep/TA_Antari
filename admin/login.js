/**
 * login.js
 * Handle semua interaksi di halaman login
 */

// Kalau udah login, langsung redirect ke dashboard
if (getToken()) {
    window.location.href = '/admin/dashboard.html';
}

// Ambil elemen-elemen yang diperlukan
const inputUsername = document.getElementById('username');
const inputPassword = document.getElementById('password');
const btnLogin = document.getElementById('btnLogin');
const btnText = document.getElementById('btn-text');
const btnLoading = document.getElementById('btn-loading');
const errorUsername = document.getElementById('error-username');
const errorPassword = document.getElementById('error-password');
const errorGlobal = document.getElementById('error-global');
const togglePassword = document.getElementById('togglePassword');

// Bisa login dengan enter juga biar enak
inputPassword.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        handleLogin();
    }
});

inputUsername.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        inputPassword.focus();
    }
});

// Toggle show/hide password
togglePassword.addEventListener('click', () => {
    const type = inputPassword.type === 'password' ? 'text' : 'password';
    inputPassword.type = type;
});

// Bersihkan error waktu user mulai ngetik lagi
inputUsername.addEventListener('input', () => {
    errorUsername.textContent = '';
});

inputPassword.addEventListener('input', () => {
    errorPassword.textContent = '';
});

// Tombol login diklik
btnLogin.addEventListener('click', handleLogin);

async function handleLogin() {
    // Reset error dulu
    errorUsername.textContent = '';
    errorPassword.textContent = '';
    errorGlobal.textContent = '';

    const username = inputUsername.value.trim();
    const password = inputPassword.value;

    // Validasi di frontend dulu sebelum kirim ke backend
    let valid = true;

    if (!username) {
        errorUsername.textContent = 'Username tidak boleh kosong';
        inputUsername.classList.add('shake');
        setTimeout(() => inputUsername.classList.remove('shake'), 300);
        valid = false;
    }

    if (!password) {
        errorPassword.textContent = 'Password tidak boleh kosong';
        inputPassword.classList.add('shake');
        setTimeout(() => inputPassword.classList.remove('shake'), 300);
        valid = false;
    }

    if (!valid) return;

    // Set loading state
    setLoading(true);

    try {
        const result = await api.post('/auth/login', { username, password });

        if (result.data.success) {
            // Simpan token dan data admin
            setToken(result.data.token);
            setAdminData(result.data.admin);

            // Redirect ke dashboard
            window.location.href = '/admin/dashboard.html';
        } else {
            errorGlobal.textContent = result.data.message || 'Login gagal';
            
            // Kasih efek shake di form
            document.querySelector('.login-form-wrapper').classList.add('shake');
            setTimeout(() => {
                document.querySelector('.login-form-wrapper').classList.remove('shake');
            }, 300);
        }
    } catch (err) {
        errorGlobal.textContent = 'Terjadi kesalahan, coba lagi nanti';
        console.error(err);
    } finally {
        setLoading(false);
    }
}

function setLoading(isLoading) {
    btnLogin.disabled = isLoading;
    btnText.style.display = isLoading ? 'none' : 'inline';
    btnLoading.style.display = isLoading ? 'inline' : 'none';
}