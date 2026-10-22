# Hermes Data API — Referensi Endpoint

Base URL lokal: `http://127.0.0.1:8790`
Base URL remote: `http://100.126.10.74:8790` (Tailscale)
Mode: **read-only** (hanya `GET`)

Cakupan: **Crypto · Forex · IDX (saham) · Cronjob**

---

## Daftar Isi

1. [Konsep](#konsep)
2. [Meta](#meta)
3. [Crypto](#crypto)
4. [Forex — OHLC & Level](#forex--ohlc--level)
5. [Forex — Journal](#forex--journal)
6. [IDX — Saham](#idx--saham)
7. [Cronjob](#cronjob)
8. [Format error](#format-error)
9. [Catatan sumber data](#catatan-sumber-data)

---

## Konsep

API ini adalah **lapisan baca** di atas modul yang sudah dipakai pipeline
trading live. Aturannya:

- Semua endpoint `GET`. Tidak ada `POST`/`PUT`/`DELETE`.
- Tidak menulis file, tidak mengubah state, tidak mengirim order.
- Respons JSON, encoding UTF-8.
- Cache in-memory dengan TTL per jenis data.
- Kalau data tidak ada → `404`. Parameter salah → `400`.
  Sumber upstream gagal → `502`.

---

## Meta

### `GET /`
Info API + peta semua endpoint (crypto, forex, forex_journal, idx, cron).

### `GET /health`
```json
{ "status": "ok", "version": "1.0.0", "mode": "read-only" }
```

### `GET /cache`
Status cache in-memory (debug).

---

## Crypto

### `GET /crypto/universe`
Daftar koin aktif (Big Cap ≥ $10B + Mid Cap $1B–$10B).

```json
{ "count": 44, "symbols": ["BTCUSDT", "ETHUSDT", "..."] }
```

### `GET /crypto/universe/{symbol}`
Info satu koin (tier market cap).

### `GET /crypto/klines`
OHLCV dari **MEXC**.

| Parameter | Default | Keterangan |
|---|---|---|
| `symbol` | wajib | `BTCUSDT` |
| `interval` | `1h` | `5m` `15m` `1h` `4h` `1d` |
| `limit` | `300` | 10–2000 |

```json
{
  "symbol": "BTCUSDT", "interval": "1h", "source": "mexc", "count": 3,
  "candles": [{ "t": 1792400400000, "o": 82786.0, "h": 83072.3,
                "l": 82700.0, "c": 82950.1, "v": 1234.5 }]
}
```
`t` = epoch milidetik (UTC).

### `GET /crypto/ticker`
Volume & harga 24 jam (**Binance Futures**).

```json
{
  "symbol": "BTCUSDT", "last_price": 83369.3, "change_pct_24h": 2.232,
  "volume_base_24h": 135553.912, "volume_quote_24h": 11305400000.0,
  "high_24h": 84100.0, "low_24h": 81200.0, "source": "binance"
}
```
`volume_quote_24h` dipakai gate likuiditas (min $50 juta).

### `GET /crypto/funding`
Funding rate + Open Interest.

```json
{
  "symbol": "BTCUSDT", "mark_price": 83373.5,
  "funding_rate": 0.0001, "funding_rate_pct": 0.01,
  "next_funding_time": 1792502400000, "open_interest": 97145.591
}
```

### `GET /crypto/sectors`
Tren per sektor dari perubahan 24 jam semua kontrak **MEXC**.

```json
{
  "source": "mexc",
  "thresholds": { "hot_pct": 3.0, "cold_pct": -3.0 },
  "sectors": [
    { "sector": "DeFi", "avg_change_24h_pct": 4.21, "coins": 9,
      "state": "HOT", "rank": 1 }
  ]
}
```
`state`: `HOT` (≥ +3%), `COLD` (≤ −3%), `NETRAL`.

### `GET /crypto/sector/{symbol}`
Sektor + narasi satu koin.

### `GET /crypto/news`
Kalender berita ekonomi. Default **hanya impact High** (aturan blackout).

| Parameter | Default | Keterangan |
|---|---|---|
| `days_ahead` | `3` | 0–14 |
| `min_impact` | `High` | `High` `Medium` `Low` |

> `actual` hampir selalu `null` — feed ForexFactory tidak menyediakan nilai
> actual. Alternatif (TradingView calendar, scrape FF) diblokir 403.

### `GET /crypto/equity`
Kurva equity + statistik dari ledger trade crypto.

### `GET /crypto/levels`
Hitung SL/TP memakai mesin yang sama dengan pipeline live.

| Parameter | Default | Keterangan |
|---|---|---|
| `symbol` | wajib | `BTCUSDT` |
| `play` | `scalping` | `scalping` \| `intraday` |
| `side` | `LONG` | `LONG` \| `SHORT` |

Aturan (21 Okt 2026):
```
SL = struktur (wick/sweep) + buffer 0.2xATR, min 2xATR
     cap keras: scalping 1.5% · intraday 2.5%
TP = dari R: scalping 1R/2R/3R (1:3) · intraday 1R/2R (1:2)
BE = intraday 1R
```

```json
{
  "symbol": "AVAXUSDT", "play": "scalping", "status": "OK",
  "atr_pct": 0.2601,
  "rules": { "sl_max_pct": 1.5, "min_atr_pct": 0.18,
             "tp1_r": 1.0, "tp2_r": 2.0, "tp3_r": 3.0 },
  "levels": {
    "entry": 9.656, "sl": 9.6058, "tp1": 9.7062, "tp2": 9.7564, "tp3": 9.8067,
    "sl_pct": 0.5201, "rr1": 1.0, "rr2": 2.0, "rr3": 3.0
  }
}
```

Ditolak (bukan error, gate bekerja):
```json
{ "status": "REJECTED", "reason": "ATR 0.170% < minimum 0.18%" }
```

### `GET /crypto/plays`
Konfigurasi play crypto aktif (scalping & intraday; SWING dihapus).

---

## Forex — OHLC & Level

Instrumen: **XAUUSD**, **NAS100**, **DXY**. OHLC dari TradingView.

### `GET /forex/instruments`
```json
{
  "source": "tradingview", "count": 3,
  "instruments": [{ "symbol": "XAUUSD", "tv": "TVC:GOLD",
                    "label": "Gold Spot", "type": "metal" }]
}
```

### `GET /forex/klines`

| Parameter | Default | Keterangan |
|---|---|---|
| `symbol` | wajib | `XAUUSD` `NAS100` `DXY` |
| `interval` | `60` | `5` `15` `60` `240` `1D` `1W` |
| `limit` | `200` | 10–1000 |

`t` = epoch **detik** (beda dari crypto yang milidetik).

### `GET /forex/dxy`
Perubahan DXY (4 bar 1H) — filter korelasi.
```json
{ "symbol": "DXY", "change_pct": -0.0344 }
```

### `GET /forex/levels`
Level SL/TP forex. Parameter sama dengan `/crypto/levels`.

### `GET /forex/plays`
Konfigurasi play forex (SCALPING & INTRADAY).

---

## Forex — Journal

Data jurnal trading XAU/NAS100 (dari dashboard XAU).

### `GET /forex/journal/stats`
Statistik journal: harga terkini, total sinyal, dsb.

### `GET /forex/journal/trades`
Trade terbuka + tertutup.

| Parameter | Default |
|---|---|
| `limit` | `50` (1–500) |

```json
{
  "price": 4099.93,
  "open": [],
  "closed": [{ "pair": "EURUSD", "id": "MP-09-23T17:00", "date_wib": "..." }]
}
```

### `GET /forex/journal/watchlist`
Watchlist forex aktif.

### `GET /forex/journal/edge`
Statistik edge per sesi/pair.
```json
{ "sessions": { "XAUUSD": { "ASIA": { "n": 1, "wins": 0, "r": -1.0,
                                      "wr": 0.0, "avg_r": -1.0 } } } }
```

### `GET /forex/journal/scanlog`
Log scan forex — alasan sinyal ditolak.

### `GET /forex/journal/performance`
Performa trading forex.

### `GET /forex/journal/session`
Sesi market sekarang.
```json
{ "now_wib": "22 Oct 2026 14:17:03", "session": "LONDON",
  "killzone": "London killzone aktif (13:00–16:00)" }
```

### `GET /forex/journal/multipair`
Ringkasan multi-pair forex.

### `GET /forex/journal/charts`
Daftar chart tersedia.

| Parameter | Default |
|---|---|
| `limit` | `8` (1–50) |

---

## IDX — Saham

Data saham Indonesia dari sistem IDX616.

### `GET /idx/stats`
```json
{
  "total_runs": 93, "unique_tickers_tracked": 311,
  "total_signals": 1753, "universe_size": 6, "latest_by_job": {}
}
```

### `GET /idx/signals`
Daftar sinyal saham.

| Parameter | Default | Keterangan |
|---|---|---|
| `preset` | semua | filter preset (mis. `swell_long_prime`) |
| `limit` | `100` | 1–500 |

```json
{
  "count": 3,
  "signals": [{ "time": "2026-09-15 09:38:24", "ticker": "BJTM",
                "preset": "swell_long_prime", "price": 1234 }]
}
```

### `GET /idx/history/{job_id}`
Riwayat sinyal per job.
| Parameter | Default |
|---|---|
| `limit` | `20` (1–200) |

### `GET /idx/latest/{job_id}`
Sinyal terakhir dari satu job.

### `GET /idx/market`
Data market IDX (sesi pre/regular/post).
| Parameter | Default |
|---|---|
| `limit` | `30` (1–200) |

### `GET /idx/flow`
Aliran dana per ticker.

| Parameter | Default | Keterangan |
|---|---|---|
| `ticker` | wajib | `BBRI` |
| `days` | `7` | 1–90 |

### `GET /idx/scanners`
Daftar scanner IDX yang aktif.

### `GET /idx/news`
Berita terkait IDX.

### `GET /idx/official`
Data resmi IDX.

### `GET /idx/feed`
Feed sinyal ringkas.
| Parameter | Default |
|---|---|
| `limit` | `50` (1–200) |

### `GET /idx/equity`
Kurva equity IDX.
```json
{
  "points": [{ "ts": "2026-09-17T13:45", "r": -1.0, "cum": -1.0,
               "result": "SL", "ticker": "PSDN.JK", "setup": "..." }],
  "n": 12, "capital": 100000000, "risk_per_r": 0.01,
  "total_r": 3.5, "win_rate": 58.3, "expectancy_r": 0.29,
  "max_drawdown_r": -2.0, "wins": 7, "losses": 5, "pending": 0
}
```

### `GET /idx/ledger`
Metrik dari ledger sinyal IDX.

---

## Cronjob

### `GET /cron/jobs`
Daftar semua cronjob.
```json
{
  "count": 49,
  "jobs": [{ "id": "481a68e283f3", "name": "crypto-auto-exec-653",
             "schedule": "* * * * *", "enabled": true,
             "script": "crypto_auto_exec.py",
             "last_run": "2026-10-22T15:15:13", "last_status": "ok" }]
}
```

### `GET /cron/jobs/{job_id}`
Detail satu job (bisa pakai id atau nama).

### `GET /cron/executions`
Riwayat eksekusi.

| Parameter | Default | Keterangan |
|---|---|---|
| `job_id` | semua | filter job |
| `limit` | `50` | 1–500 |

### `GET /cron/summary`
Ringkasan status.
```json
{
  "total": 49, "enabled": 17, "disabled": 32,
  "last_ok": 48, "last_failed": 1, "jobs": []
}
```

---

## Format error

```json
{ "detail": "pesan jelas dalam bahasa manusia" }
```

| Kode | Arti |
|---|---|
| `400` | parameter tidak valid |
| `404` | simbol/data/job tidak ditemukan |
| `502` | sumber upstream gagal |

---

## Catatan sumber data

| Data | Sumber |
|---|---|
| Crypto OHLCV | MEXC |
| Crypto volume/OI/funding | Binance Futures |
| Tren sektor crypto | MEXC |
| Forex OHLC | TradingView |
| Berita ekonomi | ForexFactory feed |
| Journal forex | Dashboard XAU (SQLite + Excel) |
| IDX saham | Sistem IDX616 (SQLite) |
| Cronjob | `~/.hermes/cron/jobs.json` + `executions.db` |

Cache TTL (detik):

```
klines 60 · ticker 30 · universe 3600 · sectors 300
news 900 · equity 120 · scan 120 · levels 60 · cron 30
```

Semua akses database memakai mode **read-only** (`mode=ro`), jadi API ini
tidak bisa merusak data meski ada bug.
