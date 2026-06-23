from flask import Flask, redirect, url_for

app = Flask(__name__, 
            static_folder='Frontend/utama', 
            template_folder='Frontend/utama')

# Jalur utama langsung diarahkan ke halaman login
@app.route('/')
def index():
    return redirect(url_for('utama_auth.login'))

# Daftarkan modul backend
from Backend.utama.auth import utama_auth
from Backend.utama.kasir import utama_kasir

app.register_blueprint(utama_auth)
app.register_blueprint(utama_kasir)

if __name__ == '__main__':
    app.run(debug=True)