# Hermes Data API — Referensi Endpoint

Base URL: `http://127.0.0.1:8790`
Mode: **read-only** (hanya `GET`)

---

## Daftar Isi

1. [Konsep](#konsep)
2. [Meta](#meta)
3. [Crypto](#crypto)
4. [Forex](#forex)
5. [Format error](#format-error)
6. [Catatan sumber data](#catatan-sumber-data)

---

## Konsep

API ini adalah **lapisan baca** di atas modul yang sudah dipakai pipeline
trading live. Aturannya:

- Semua endpoint `GET`. Tidak ada `POST`/`PUT`/`DELETE`.
- Tidak menulis file, tidak mengubah state, tidak mengirim order.
- Respons JSON, encoding UTF-8.
- Cache in-memory dengan TTL: klines 60s, ticker 30s, sektor 300s,
  berita 900s, level 60s, universe 3600s.
- Kalau data tidak ada → `404`. Kalau parameter salah → `400`.
  Kalau sumber upstream gagal → `502`.

---

## Meta

### `GET /`

Info API + peta endpoint.

```json
{
  "name": "Hermes Data API",
  "version": "1.0.0",
  "mode": "read-only",
  "docs": "/docs",
  "openapi": "/openapi.json",
  "endpoints": {
    "crypto": ["/crypto/universe", "/crypto/klines", "..."],
    "forex": ["/forex/instruments", "/forex/klines", "..."],
    "system": ["/health", "/cache"]
  }
}
```

### `GET /health`

```json
{ "status": "ok", "version": "1.0.0", "mode": "read-only" }
```

### `GET /cache`

Status cache in-memory (untuk debugging).

```json
{
  "entries": 3,
  "keys": [
    { "key": "kl:BTCUSDT:1h:300", "age_s": 12.4 },
    { "key": "tk:BTCUSDT", "age_s": 3.1 }
  ]
}
```

---

## Crypto

### `GET /crypto/universe`

Daftar koin yang dipakai sistem (Big Cap ≥ $10B + Mid Cap $1B–$10B).

```json
{
  "count": 44,
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "..."]
}
```

### `GET /crypto/universe/{symbol}`

Info satu koin (tier market cap, dsb).

```bash
curl "http://127.0.0.1:8790/crypto/universe/BTCUSDT"
```

### `GET /crypto/klines`

OHLCV dari **MEXC** (sumber analisis + eksekusi).

| Parameter | Wajib | Default | Keterangan |
|---|---|---|---|
| `symbol` | ya | — | contoh `BTCUSDT` |
| `interval` | tidak | `1h` | `5m` `15m` `1h` `4h` `1d` |
| `limit` | tidak | `300` | 10–2000 candle |

```bash
curl "http://127.0.0.1:8790/crypto/klines?symbol=BTCUSDT&interval=1h&limit=3"
```

```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "source": "mexc",
  "count": 3,
  "candles": [
    { "t": 1792400400000, "o": 82786.0, "h": 83072.3, "l": 82700.0, "c": 82950.1, "v": 1234.5 }
  ]
}
```

`t` = epoch milidetik (UTC). `v` = volume base asset.

### `GET /crypto/ticker`

Volume & harga 24 jam dari **Binance Futures**.

| Parameter | Wajib | Keterangan |
|---|---|---|
| `symbol` | ya | contoh `BTCUSDT` |

```json
{
  "symbol": "BTCUSDT",
  "last_price": 83369.3,
  "change_pct_24h": 2.232,
  "volume_base_24h": 135553.912,
  "volume_quote_24h": 11305400000.0,
  "high_24h": 84100.0,
  "low_24h": 81200.0,
  "source": "binance"
}
```

`volume_quote_24h` dipakai untuk gate likuiditas (minimal $50 juta).

### `GET /crypto/funding`

Funding rate + Open Interest dari **Binance Futures**.

```json
{
  "symbol": "BTCUSDT",
  "mark_price": 83373.5,
  "funding_rate": 0.0001,
  "funding_rate_pct": 0.01,
  "next_funding_time": 1792502400000,
  "open_interest": 97145.591,
  "source": "binance"
}
```

### `GET /crypto/sectors`

Tren per sektor, dihitung dari perubahan 24 jam semua kontrak **MEXC**.

```json
{
  "source": "mexc",
  "thresholds": { "hot_pct": 3.0, "cold_pct": -3.0 },
  "sectors": [
    { "sector": "DeFi", "avg_change_24h_pct": 4.21, "coins": 9, "state": "HOT", "rank": 1 },
    { "sector": "L1", "avg_change_24h_pct": 1.80, "coins": 11, "state": "NETRAL", "rank": 2 },
    { "sector": "Gaming", "avg_change_24h_pct": -3.42, "coins": 6, "state": "COLD", "rank": 6 }
  ]
}
```

`state`: `HOT` kalau rata-rata ≥ +3%, `COLD` kalau ≤ −3%, selain itu `NETRAL`.

### `GET /crypto/sector/{symbol}`

Sektor + narasi satu koin.

```json
{
  "symbol": "UNIUSDT",
  "sector": "DeFi",
  "narrative": { "sector": "DeFi", "avg_pct": 4.21, "state": "HOT", "score": 1 }
}
```

### `GET /crypto/news`

Kalender berita ekonomi. **Default hanya impact High** (sesuai aturan
blackout sistem: hanya High yang memblokir entry).

| Parameter | Default | Keterangan |
|---|---|---|
| `days_ahead` | `3` | 0–14 hari |
| `min_impact` | `High` | `High` `Medium` `Low` |

```json
{
  "filter": { "days_ahead": 3, "min_impact": "High" },
  "count": 1,
  "events": [
    {
      "title": "CPI y/y",
      "country": "GBP",
      "impact": "High",
      "time_utc": "2026-10-21T07:00:00+00:00",
      "time_wib": "2026-10-21 14:00 WIB",
      "ts": 1792566000,
      "minutes_to": 132,
      "forecast": "3.1%",
      "previous": "3.0%",
      "actual": null,
      "verdict": "belum rilis"
    }
  ]
}
```

> **Catatan jujur:** field `actual` hampir selalu `null`. Feed ForexFactory
> yang dipakai tidak menyediakan nilai actual; sudah dicoba beberapa sumber
> alternatif (TradingView calendar, scrape ForexFactory) tapi diblokir 403.
> Untuk nilai actual perlu sumber berbayar.

### `GET /crypto/equity`

Kurva equity + statistik dari ledger trade.

```json
{
  "points": [
    { "i": 0, "r": 0.0, "cum": 0.0, "label": "start", "signal_id": null },
    { "i": 1, "r": 1.0, "cum": 1.0, "label": "closed_TP1", "signal_id": "#SIG6BA6F536", "pair": "AVAXUSDT" }
  ],
  "trades": 12,
  "stats": { "win_rate": 66.7, "total_r": 8.5, "avg_r": 0.71 },
  "since": "2026-10-01"
}
```

### `GET /crypto/levels`

Hitung level SL/TP untuk satu koin memakai mesin yang sama dengan pipeline
live. Berguna untuk memverifikasi aturan tanpa menjalankan scan penuh.

| Parameter | Default | Keterangan |
|---|---|---|
| `symbol` | wajib | contoh `BTCUSDT` |
| `play` | `scalping` | `scalping` atau `intraday` |
| `side` | `LONG` | `LONG` atau `SHORT` |

**Aturan yang dipakai (per 21 Okt 2026):**

```
SL  = struktur (wick/sweep) + buffer 0.2xATR, minimal 2xATR
      cap keras: scalping 1.5% · intraday 2.5%
TP  = dari R (jarak SL aktual)
      scalping: 1R / 2R / 3R   (1:3)
      intraday: 1R / 2R        (1:2)
BE  = intraday 1R
```

Contoh sukses:

```bash
curl "http://127.0.0.1:8790/crypto/levels?symbol=AVAXUSDT&play=scalping"
```

```json
{
  "symbol": "AVAXUSDT",
  "play": "scalping",
  "side": "LONG",
  "tf": "5m",
  "price": 9.656,
  "atr": 0.0251,
  "atr_pct": 0.2601,
  "rules": { "sl_max_pct": 1.5, "min_atr_pct": 0.18,
             "tp1_r": 1.0, "tp2_r": 2.0, "tp3_r": 3.0 },
  "status": "OK",
  "levels": {
    "entry": 9.656,
    "sl": 9.6058,
    "tp1": 9.7062,
    "tp2": 9.7564,
    "tp3": 9.8067,
    "sl_pct": 0.5201,
    "risk": 0.0502,
    "sweep": false,
    "pullback": false,
    "rr1": 1.0, "rr2": 2.0, "rr3": 3.0,
    "rr_note": "R:R 1:2.00 (TP2) · 1:1.00 (TP1) · TP 1R/2R",
    "note": "SL LONG di balik low 12 bar (9.652) + buffer 0.2xATR = 0.52%"
  }
}
```

Contoh ditolak (ATR terlalu tenang):

```json
{
  "symbol": "ETHUSDT",
  "play": "scalping",
  "atr_pct": 0.1698,
  "rules": { "min_atr_pct": 0.18, "sl_max_pct": 1.5 },
  "status": "REJECTED",
  "reason": "ATR 0.170% < minimum 0.18%"
}
```

Status `REJECTED` **bukan error** — itu gate yang bekerja. Alasannya selalu
dijelaskan di field `reason`.

### `GET /crypto/plays`

Konfigurasi play crypto aktif.

```json
{
  "order": ["scalping", "intraday"],
  "plays": {
    "scalping": {
      "label": "SCALPING",
      "tf": ["5m", "15m", "1h"],
      "primary_tf": "5m",
      "hold_hours": [1, 4],
      "sl_max_pct": 1.5,
      "min_atr_pct": 0.18,
      "tp1_r": 1.0, "tp2_r": 2.0, "tp3_r": 3.0
    },
    "intraday": {
      "label": "INTRADAY",
      "tf": ["1d", "4h", "1h"],
      "primary_tf": "1h",
      "hold_hours": [4, 24],
      "sl_max_pct": 2.5,
      "min_atr_pct": 0.15,
      "tp1_r": 1.0, "tp2_r": 2.0
    }
  }
}
```

> SWING sudah dihapus total 21 Okt 2026.

---

## Forex

Instrumen yang tersedia: **XAUUSD** (Gold), **NAS100** (Nasdaq 100),
**DXY** (Dollar Index). Data OHLC dari TradingView.

### `GET /forex/instruments`

```json
{
  "source": "tradingview",
  "count": 3,
  "instruments": [
    { "symbol": "XAUUSD", "tv": "TVC:GOLD", "label": "Gold Spot",
      "type": "metal", "timeframes": ["15", "1D", "1W", "240", "5", "60"] }
  ]
}
```

### `GET /forex/klines`

| Parameter | Default | Keterangan |
|---|---|---|
| `symbol` | wajib | `XAUUSD` `NAS100` `DXY` |
| `interval` | `60` | `5` `15` `60` `240` `1D` `1W` |
| `limit` | `200` | 10–1000 bar |

```json
{
  "symbol": "XAUUSD",
  "tv_symbol": "TVC:GOLD",
  "interval": "60",
  "source": "tradingview",
  "count": 30,
  "candles": [
    { "t": 1792468800, "o": 4146.13, "h": 4147.21, "l": 4140.5, "c": 4142.9, "v": 199208.0 }
  ]
}
```

`t` = epoch **detik** (berbeda dari crypto yang milidetik).

### `GET /forex/dxy`

Perubahan DXY (4 bar 1H) — dipakai sebagai filter korelasi.

```json
{ "symbol": "DXY", "change_pct": -0.0344, "source": "tradingview" }
```

### `GET /forex/levels`

Level SL/TP forex. Parameter sama dengan `/crypto/levels`.

```bash
curl "http://127.0.0.1:8790/forex/levels?symbol=XAUUSD&play=scalping&side=LONG"
```

```json
{
  "symbol": "XAUUSD",
  "play": "scalping",
  "side": "LONG",
  "tf": "5",
  "price": 4116.34,
  "atr": 3.7399,
  "atr_pct": 0.0909,
  "rules": { "sl_max_pct": 2.0, "min_atr_pct": 0.03, "tp1_r": 1.0, "tp2_r": 1.5 },
  "status": "OK",
  "levels": { "entry": 4116.34, "sl": 4109.5, "tp1": 4123.2, "tp2": 4126.6 }
}
```

### `GET /forex/plays`

```json
{
  "order": ["SCALPING", "INTRADAY"],
  "plays": {
    "scalping": {
      "label": "SCALPING",
      "tf": ["60", "15", "5", "240"],
      "tf_label": ["1H", "15M", "5M", "4H"],
      "primary_tf": "5",
      "bias_tf": "60",
      "sl_max_pct": 2.0,
      "min_atr_pct": 0.03,
      "tp1_r": 1.0,
      "tp2_r": 1.5
    }
  }
}
```

---

## Format error

Semua error memakai format FastAPI standar:

```json
{ "detail": "pesan jelas dalam bahasa manusia" }
```

| Kode | Arti |
|---|---|
| `400` | parameter tidak valid (play/side/interval salah) |
| `404` | simbol atau data tidak ditemukan |
| `502` | sumber upstream (MEXC/Binance/TradingView) gagal |

Contoh:

```json
{ "detail": "instrumen tidak dikenal: EURUSD. Pilih: XAUUSD, NAS100, DXY" }
{ "detail": "play harus 'scalping' atau 'intraday'" }
{ "detail": "symbol tidak ada di universe: FOOUSDT" }
```

---

## Catatan sumber data

| Data | Sumber | Kenapa |
|---|---|---|
| Crypto OHLCV | MEXC | sama dengan bursa eksekusi, selisih harga vs Binance hanya 0.010% |
| Crypto volume 24H / 15M | Binance Futures | likuiditas lebih representatif untuk gate |
| Crypto OI + funding | Binance Futures | data derivatif terlengkap |
| Tren sektor | MEXC | dihitung dari bursa yang sama dengan eksekusi |
| Forex OHLC | TradingView | sistem XAU/NAS100 terpisah, hanya dibaca |
| Berita ekonomi | ForexFactory feed | satu-satunya yang stabil & gratis |

Cache TTL (detik):

```
klines 60 · ticker 30 · universe 3600 · sectors 300
news 900 · equity 120 · levels 60
```

Untuk memaksa data segar, tunggu TTL habis. Tidak ada parameter bypass cache
karena API ini read-only dan dipakai bersama.
