"""
app.py — ProactiveMail Web — Flask ana uygulama.

Çalıştırma:
    pip install flask flask-cors
    python app.py

Tarayıcı: http://localhost:5000
"""

from flask import Flask, send_from_directory
from flask_cors import CORS

from config import SECRET_KEY, HOST, PORT, DEBUG, DB_PATH
from proactivemail.db import Database

# Uygulama
app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = SECRET_KEY
CORS(app)

#  Veritabanı (uygulama genelinde tek instance) 
db = Database(DB_PATH)
db.init()
app.config["DB"] = db

#  API blueprint'leri 
from api.recipients import bp as recipients_bp
from api.campaigns  import bp as campaigns_bp
from api.send       import bp as send_bp
from api.settings   import bp as settings_bp
from api.logs       import bp as logs_bp

app.register_blueprint(recipients_bp, url_prefix="/api")
app.register_blueprint(campaigns_bp,  url_prefix="/api")
app.register_blueprint(send_bp,       url_prefix="/api")
app.register_blueprint(settings_bp,   url_prefix="/api")
app.register_blueprint(logs_bp,       url_prefix="/api")

#  SPA catch-all: tüm GET isteklerini index.html'e yönlendir 
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    return send_from_directory(app.static_folder, "index.html")

#  Giriş noktası 
if __name__ == "__main__":
    print(f"ProactiveMail Web  →  http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=DEBUG)
