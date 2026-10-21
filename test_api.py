#!/usr/bin/env python3
"""Smoke test semua endpoint Hermes Data API.

Jalankan: python test_api.py [base_url]
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8790"

CASES = [
    # (path, harapan_status)
    ("/", 200),
    ("/health", 200),
    ("/cache", 200),
    ("/crypto/universe", 200),
    ("/crypto/universe/BTCUSDT", 200),
    ("/crypto/plays", 200),
    ("/crypto/sectors", 200),
    ("/crypto/sector/UNIUSDT", 200),
    ("/crypto/ticker?symbol=BTCUSDT", 200),
    ("/crypto/funding?symbol=BTCUSDT", 200),
    ("/crypto/klines?symbol=BTCUSDT&interval=1h&limit=20", 200),
    ("/crypto/news?days_ahead=3", 200),
    ("/crypto/equity", 200),
    ("/crypto/levels?symbol=AVAXUSDT&play=scalping", 200),
    ("/forex/instruments", 200),
    ("/forex/plays", 200),
    ("/forex/dxy", 200),
    ("/forex/klines?symbol=XAUUSD&interval=60&limit=20", 200),
    ("/forex/levels?symbol=XAUUSD&play=scalping", 200),
    # error handling
    ("/forex/klines?symbol=EURUSD", 404),
    ("/crypto/levels?symbol=BTCUSDT&play=swing", 400),
    ("/crypto/universe/FOOUSDT", 404),
]


def get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=120) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None
    except Exception as e:
        return 0, {"exception": f"{type(e).__name__}: {e}"}


def main():
    ok = fail = 0
    for path, want in CASES:
        code, body = get(path)
        good = code == want
        ok += good
        fail += not good
        mark = "OK  " if good else "FAIL"
        extra = ""
        if isinstance(body, dict):
            for k in ("count", "status", "detail", "mode"):
                if k in body:
                    extra = f" {k}={body[k]}"
                    break
        print(f"{mark} {code:3} {path}{extra}")
    print(f"\n{ok} ok · {fail} gagal · total {len(CASES)}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
