"""
config.py — ProactiveMail Web uygulama ayarları.
"""
import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "proactivemail.db")
SECRET_KEY = os.environ.get("PM_SECRET", "proactivemail-dev-secret-change-me")
HOST       = os.environ.get("PM_HOST", "0.0.0.0")
PORT       = int(os.environ.get("PM_PORT", 5000))
DEBUG      = os.environ.get("PM_DEBUG", "1") == "1"
