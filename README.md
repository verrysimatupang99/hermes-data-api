# Hermes Data API

API **read-only** untuk semua data Crypto & Forex di sistem Hermes.

Tidak ada endpoint yang menulis, mengubah, atau mengeksekusi order. Semua
fungsi hanya membaca dari sumber yang sudah dipakai pipeline live.

- Base URL lokal: `http://127.0.0.1:8790`
- Dokumentasi interaktif: `/docs` (Swagger UI)
- OpenAPI schema: `/openapi.json`

## Quick start

```bash
cd /home/ubuntu/hermes-data-api
/home/ubuntu/hermes-agent/venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8790
```

Buka `http://127.0.0.1:8790/docs`.

## Contoh

```bash
# daftar koin
curl "http://127.0.0.1:8790/crypto/universe"

# OHLCV BTC 1 jam
curl "http://127.0.0.1:8790/crypto/klines?symbol=BTCUSDT&interval=1h&limit=100"

# level SL/TP intraday
curl "http://127.0.0.1:8790/crypto/levels?symbol=BTCUSDT&play=intraday"

# tren sektor
curl "http://127.0.0.1:8790/crypto/sectors"

# gold 1 jam
curl "http://127.0.0.1:8790/forex/klines?symbol=XAUUSD&interval=60&limit=50"
```

Dokumentasi lengkap tiap endpoint: lihat [API.md](API.md).
