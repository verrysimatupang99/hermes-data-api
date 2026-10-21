"""Konfigurasi terpusat."""
import os

SCRIPTS = os.environ.get("HERMES_SCRIPTS", "/home/ubuntu/.hermes/scripts")
HOST = os.environ.get("API_HOST", "127.0.0.1")
PORT = int(os.environ.get("API_PORT", "8790"))

# Cache TTL detik per jenis data (read-only, aman di-cache)
TTL = {
    "klines": 60,
    "ticker": 30,
    "universe": 3600,
    "sectors": 300,
    "news": 900,
    "equity": 120,
    "scan": 120,
    "levels": 60,
}

CORS = os.environ.get("API_CORS", "*")
