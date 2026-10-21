"""Sumber data crypto — pembungkus tipis di atas modul pipeline live.

Semua fungsi di sini READ-ONLY: hanya memanggil fungsi baca yang sudah ada.
"""
import sys

from .config import SCRIPTS

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


# --- OHLCV: MEXC (sumber utama analisis + eksekusi) -------------------------
def klines(symbol: str, interval: str = "1h", limit: int = 300) -> dict:
    import mexc_feed
    d = mexc_feed.fetch_klines(symbol, interval, limit)
    if not d:
        raise LookupError(f"klines tidak tersedia untuk {symbol} {interval}")
    ts = d.get("timestamps") or []
    n = len(d["closes"])
    candles = [
        {
            "t": int(ts[i]) if i < len(ts) else None,
            "o": d["opens"][i],
            "h": d["highs"][i],
            "l": d["lows"][i],
            "c": d["closes"][i],
            "v": d["volumes"][i],
        }
        for i in range(n)
    ]
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "source": d.get("source", "mexc"),
        "count": n,
        "candles": candles,
    }


# --- Universe ---------------------------------------------------------------
def universe() -> list:
    import universe as u
    return u.get()


def universe_info(symbol: str) -> dict | None:
    import universe as u
    return u.info(symbol)


# --- Volume 24H + OI + funding: Binance ------------------------------------
def ticker(symbol: str) -> dict:
    import json
    import urllib.request
    url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol.upper()}"
    with urllib.request.urlopen(url, timeout=15) as r:
        d = json.load(r)
    return {
        "symbol": d.get("symbol"),
        "last_price": float(d.get("lastPrice", 0)),
        "change_pct_24h": float(d.get("priceChangePercent", 0)),
        "volume_base_24h": float(d.get("volume", 0)),
        "volume_quote_24h": float(d.get("quoteVolume", 0)),
        "high_24h": float(d.get("highPrice", 0)),
        "low_24h": float(d.get("lowPrice", 0)),
        "source": "binance",
    }


def funding(symbol: str) -> dict:
    import json
    import urllib.request
    base = "https://fapi.binance.com/fapi/v1"
    with urllib.request.urlopen(f"{base}/premiumIndex?symbol={symbol.upper()}", timeout=15) as r:
        p = json.load(r)
    with urllib.request.urlopen(f"{base}/openInterest?symbol={symbol.upper()}", timeout=15) as r:
        o = json.load(r)
    return {
        "symbol": p.get("symbol"),
        "mark_price": float(p.get("markPrice", 0)),
        "funding_rate": float(p.get("lastFundingRate", 0)),
        "funding_rate_pct": float(p.get("lastFundingRate", 0)) * 100,
        "next_funding_time": p.get("nextFundingTime"),
        "open_interest": float(o.get("openInterest", 0)),
        "source": "binance",
    }


# --- Sektor / tren ---------------------------------------------------------
def sectors() -> dict:
    import sector_flow as sf
    changes = sf._fetch_24h()
    from collections import defaultdict
    bucket = defaultdict(list)
    for sym, pct in changes.items():
        bucket[sf.sector_of(sym)].append(pct)
    rows = []
    for name, vals in bucket.items():
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        if avg >= sf.HOT_PCT:
            state = "HOT"
        elif avg <= sf.COLD_PCT:
            state = "COLD"
        else:
            state = "NETRAL"
        rows.append({
            "sector": name,
            "avg_change_24h_pct": round(avg, 2),
            "coins": len(vals),
            "state": state,
        })
    rows.sort(key=lambda x: -x["avg_change_24h_pct"])
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return {
        "source": "mexc",
        "thresholds": {"hot_pct": sf.HOT_PCT, "cold_pct": sf.COLD_PCT},
        "sectors": rows,
    }


def sector_of(symbol: str) -> dict:
    import sector_flow as sf
    return {
        "symbol": symbol.upper(),
        "sector": sf.sector_of(symbol),
        "narrative": sf.narrative(symbol),
    }


# --- Berita ekonomi --------------------------------------------------------
def news(days_ahead: int = 3, min_impact: str = "High") -> dict:
    import news_calendar as nc
    ev = nc.events(days_ahead=days_ahead, min_impact=min_impact)
    return {
        "filter": {"days_ahead": days_ahead, "min_impact": min_impact},
        "count": len(ev),
        "events": ev,
    }


# --- Equity / riwayat ------------------------------------------------------
def equity() -> dict:
    import crypto_equity as ce
    return ce.curve()


# --- Level SL/TP dari mesin play ------------------------------------------
def levels(symbol: str, play: str = "scalping", side: str = "LONG") -> dict:
    import indicators as ind
    import play_scan as PS
    import plays

    p = plays.get(play)
    if not p:
        raise LookupError(f"play tidak dikenal: {play}")
    tf = p["primary_tf"]
    kl = klines(symbol, tf, 300)
    highs = [c["h"] for c in kl["candles"]]
    lows = [c["l"] for c in kl["candles"]]
    closes = [c["c"] for c in kl["candles"]]
    vols = [c["v"] for c in kl["candles"]]
    sn = ind.snapshot(highs, lows, closes, vols)
    px = closes[-1]
    atr_pct = sn["atr"] / px * 100 if px else 0
    out = {
        "symbol": symbol.upper(),
        "play": play,
        "side": side.upper(),
        "tf": tf,
        "price": px,
        "atr": sn["atr"],
        "atr_pct": round(atr_pct, 4),
        "rules": {
            "sl_max_pct": p.get("sl_max_pct"),
            "min_atr_pct": p.get("min_atr_pct"),
            "tp1_r": p.get("tp1_r"),
            "tp2_r": p.get("tp2_r"),
            "tp3_r": p.get("tp3_r"),
        },
    }
    if atr_pct < p.get("min_atr_pct", 0):
        out["status"] = "REJECTED"
        out["reason"] = f"ATR {atr_pct:.3f}% < minimum {p['min_atr_pct']}%"
        return out
    lv = PS.build_levels(symbol.upper(), p, sn, side.upper(), px,
                         highs=highs, lows=lows, atr_ref=sn["atr"])
    if not lv:
        out["status"] = "REJECTED"
        out["reason"] = "level tidak bisa dibangun (SL di luar cap / pullback terlalu jauh)"
        return out
    out["status"] = "OK"
    out["levels"] = lv
    return out


# --- Play config -----------------------------------------------------------
def plays_config() -> dict:
    import plays
    return {
        "order": plays.ORDER,
        "plays": {
            k: {
                "label": v["label"],
                "tf": v["tf"],
                "tf_label": v["tf_label"],
                "primary_tf": v["primary_tf"],
                "hold_hours": v["hold_hours"],
                "sl_max_pct": v.get("sl_max_pct"),
                "min_atr_pct": v.get("min_atr_pct"),
                "tp1_r": v.get("tp1_r"),
                "tp2_r": v.get("tp2_r"),
                "tp3_r": v.get("tp3_r"),
                "risk_note": v.get("risk_note"),
            }
            for k, v in plays.PLAYS.items()
        },
    }
