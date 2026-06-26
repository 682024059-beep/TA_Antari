from flask import Flask, redirect, url_for

from Backend.utama.auth import utama_auth
from Backend.utama.kasir import utama_kasir

app = Flask(
    __name__,
    static_folder='Frontend/utama',
    template_folder='Frontend/utama'
)

app.secret_key = 'antari-coffee-secret-key'


@app.route('/')
def index():
    return redirect(url_for('utama_auth.login'))


app.register_blueprint(utama_auth)
app.register_blueprint(utama_kasir)


if __name__ == '__main__':
    app.run(debug=True)