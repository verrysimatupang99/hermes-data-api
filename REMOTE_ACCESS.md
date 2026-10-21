# Akses dari Luar (Remote Access)

API ini **tidak terbuka ke internet publik**. Akses dari luar hanya lewat
**Tailscale** (private mesh VPN).

## URL

```
http://100.126.10.74:8790           # IP Tailscale
http://vm-0-10-ubuntu.tail3e1951.ts.net:8790   # MagicDNS
```

Port `8790`. Tidak ada HTTPS — trafik sudah terenkripsi WireGuard di level
Tailscale, jadi tidak perlu TLS tambahan.

## Syarat di laptop kamu

1. Install Tailscale: https://tailscale.com/download
2. Login dengan akun yang sama (`immanuelsimatupang99@`)
3. Pastikan device-nya muncul di `tailscale status`

Cek koneksi:

```bash
tailscale status | grep vm-0-10
curl http://100.126.10.74:8790/health
```

Harus balas `{"status":"ok",...}`.

## Contoh pemakaian dari laptop

```bash
BASE=http://100.126.10.74:8790

# daftar koin
curl "$BASE/crypto/universe"

# OHLCV BTC
curl "$BASE/crypto/klines?symbol=BTCUSDT&interval=1h&limit=100"

# level SL/TP
curl "$BASE/crypto/levels?symbol=AVAXUSDT&play=scalping"

# sektor
curl "$BASE/crypto/sectors"

# gold
curl "$BASE/forex/klines?symbol=XAUUSD&interval=60&limit=50"
```

Python:

```python
import requests
BASE = "http://100.126.10.74:8790"
r = requests.get(f"{BASE}/crypto/klines",
                 params={"symbol": "BTCUSDT", "interval": "1h", "limit": 100})
print(r.json()["count"])
```

Buka dokumentasi interaktif dari browser laptop:

```
http://100.126.10.74:8790/docs
```

## Kenapa tidak buka ke internet publik

Data ini adalah infrastruktur trading internal. Membukanya ke publik berarti:

- siapa pun bisa melihat strategi, level SL/TP, dan posisi kamu
- permukaan serangan jadi jauh lebih besar (tanpa auth = siapa pun bisa tarik
  data sebanyak-banyaknya)

Tailscale memberi akses hanya ke device yang login di tailnet kamu, dan
trafiknya terenkripsi. Ini pilihan yang tepat untuk API tanpa autentikasi.

## Kalau butuh akses dari device tanpa Tailscale

Perlu reverse proxy + API key. Belum dipasang karena belum dibutuhkan.
Kalau nanti perlu, opsi yang masuk akal:

1. **Cloudflare Tunnel + API key** — domain publik, tapi ada auth header
2. **Nginx + basic auth + rate limit** di depan port 8790
3. **Tailscale Funnel** — publik, tapi tetap bisa dibatasi

Ketiganya butuh keputusan kamu dulu karena mengubah postur keamanan.

## Verifikasi isolasi

```
bind address : 100.126.10.74 (IP Tailscale saja)
127.0.0.1    : tidak listen (sudah dicek, connection refused)
IP publik    : tidak listen (sudah dicek, timeout)
```

Server hanya mendengar di interface Tailscale, jadi tidak ada jalan masuk dari
internet meskipun firewall server sedang tidak aktif.
