"""Sumber data forex (XAUUSD, NAS100) — read-only.

Data OHLC dari TradingView via tv_feed.py (sistem XAU terpisah, hanya dibaca).
"""
import json
import os
import subprocess
import sys

from .config import SCRIPTS

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

VENV_PY = os.environ.get("HERMES_PY", "/home/ubuntu/hermes-agent/venv/bin/python")
TV_FEED = os.path.join(SCRIPTS, "tv_feed.py")

# Simbol yang tersedia di sistem forex
INSTRUMENTS = {
    "XAUUSD": {"tv": "TVC:GOLD", "label": "Gold Spot", "type": "metal"},
    "NAS100": {"tv": "CAPITALCOM:NAS100", "label": "Nasdaq 100", "type": "index"},
    "DXY": {"tv": "TVC:DXY", "label": "Dollar Index", "type": "index"},
}

# timeframe TradingView yang didukung
TF_VALID = {"5", "15", "60", "240", "1D", "1W"}


def _fetch_tv(tv_symbol: str, tf: str, bars: int) -> list | None:
    try:
        r = subprocess.run(
            [VENV_PY, TV_FEED, tv_symbol, tf, str(bars)],
            capture_output=True, text=True, timeout=75,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        d = json.loads(r.stdout)
        return d if isinstance(d, list) and len(d) >= 5 else None
    except Exception:
        return None


def instruments() -> dict:
    return {
        "source": "tradingview",
        "count": len(INSTRUMENTS),
        "instruments": [
            {"symbol": k, **v, "timeframes": sorted(TF_VALID)}
            for k, v in INSTRUMENTS.items()
        ],
    }


def klines(symbol: str, interval: str = "60", limit: int = 200) -> dict:
    sym = symbol.upper()
    if sym not in INSTRUMENTS:
        raise LookupError(f"instrumen tidak dikenal: {symbol}. "
                          f"Pilih: {', '.join(INSTRUMENTS)}")
    if interval not in TF_VALID:
        raise LookupError(f"timeframe tidak valid: {interval}. "
                          f"Pilih: {', '.join(sorted(TF_VALID))}")
    rows = _fetch_tv(INSTRUMENTS[sym]["tv"], interval, limit)
    if not rows:
        raise LookupError(f"data tidak tersedia untuk {sym} {interval}")
    return {
        "symbol": sym,
        "tv_symbol": INSTRUMENTS[sym]["tv"],
        "interval": interval,
        "source": "tradingview",
        "count": len(rows),
        "candles": rows,
    }


def dxy_change() -> dict:
    import fx_scan
    pct = fx_scan.dxy_change()
    return {"symbol": "DXY", "change_pct": pct, "source": "tradingview"}


def plays_config() -> dict:
    import fx_plays as FP
    return {
        "order": [p["label"] for p in FP.all_plays()],
        "plays": {
            k: {
                "label": v["label"],
                "tf": v["tf"],
                "tf_label": v["tf_label"],
                "primary_tf": v["primary_tf"],
                "bias_tf": v["bias_tf"],
                "hold_hours": v["hold_hours"],
                "sl_max_pct": v.get("sl_max_pct"),
                "min_atr_pct": v.get("min_atr_pct"),
                "tp1_r": v.get("tp1_r"),
                "tp2_r": v.get("tp2_r"),
                "risk_note": v.get("risk_note"),
            }
            for k, v in FP.PLAYS.items()
        },
    }


def levels(symbol: str, play: str = "scalping", side: str = "LONG") -> dict:
    import fx_plays as FP
    import fx_scan
    import indicators as ind

    p = FP.get(play)
    if not p:
        raise LookupError(f"play tidak dikenal: {play}")
    sym = symbol.upper()
    if sym not in INSTRUMENTS:
        raise LookupError(f"instrumen tidak dikenal: {symbol}")
    tf = p["primary_tf"]
    rows = _fetch_tv(INSTRUMENTS[sym]["tv"], tf, 200)
    if not rows:
        raise LookupError(f"data tidak tersedia untuk {sym}")
    highs = [r["h"] for r in rows]
    lows = [r["l"] for r in rows]
    closes = [r["c"] for r in rows]
    vols = [r.get("v", 0) for r in rows]
    sn = ind.snapshot(highs, lows, closes, vols)
    px = closes[-1]
    atr_pct = sn["atr"] / px * 100 if px else 0
    out = {
        "symbol": sym,
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
        },
    }
    min_atr = FP.min_atr_pct(sym, play)
    if atr_pct < min_atr:
        out["status"] = "REJECTED"
        out["reason"] = f"ATR {atr_pct:.3f}% < minimum {min_atr}%"
        return out
    lv = fx_scan.build_levels(sym, p, rows, side.upper(), sn["atr"], px)
    if not lv:
        out["status"] = "REJECTED"
        out["reason"] = "level tidak bisa dibangun"
        return out
    out["status"] = "OK"
    out["levels"] = lv
    return out
