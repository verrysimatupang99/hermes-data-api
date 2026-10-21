"""Hermes Data API — read-only REST untuk Crypto & Forex.

Jalankan:  uvicorn app.main:app --host 127.0.0.1 --port 8790
Docs:      http://127.0.0.1:8790/docs
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__, cache
from .config import CORS, TTL
from . import sources_crypto as C
from . import sources_forex as F

app = FastAPI(
    title="Hermes Data API",
    version=__version__,
    description=(
        "API **read-only** untuk data Crypto & Forex milik sistem Hermes.\n\n"
        "Semua endpoint hanya membaca — tidak ada order, tidak ada tulis file, "
        "tidak ada perubahan state trading.\n\n"
        "**Sumber data**\n"
        "- Crypto OHLCV: MEXC (`contract.mexc.com`)\n"
        "- Crypto volume/OI/funding: Binance Futures\n"
        "- Forex OHLC: TradingView\n"
        "- Berita ekonomi: ForexFactory feed\n"
    ),
    contact={"name": "Hermes Trading System"},
    license_info={"name": "Private / Read-Only"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS] if CORS != "*" else ["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _guard(fn, *a, **kw):
    """Bungkus pemanggilan supaya error jadi HTTP yang jelas."""
    try:
        return fn(*a, **kw)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502,
                            detail=f"{type(e).__name__}: {e}")


# ============================ META =========================================
@app.get("/", tags=["meta"], summary="Info API")
def root():
    return {
        "name": "Hermes Data API",
        "version": __version__,
        "mode": "read-only",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "crypto": ["/crypto/universe", "/crypto/klines", "/crypto/ticker",
                       "/crypto/funding", "/crypto/sectors", "/crypto/news",
                       "/crypto/equity", "/crypto/levels", "/crypto/plays"],
            "forex": ["/forex/instruments", "/forex/klines", "/forex/dxy",
                      "/forex/levels", "/forex/plays"],
            "system": ["/health", "/cache"],
        },
    }


@app.get("/health", tags=["meta"], summary="Health check")
def health():
    return {"status": "ok", "version": __version__, "mode": "read-only"}


@app.get("/cache", tags=["meta"], summary="Status cache in-memory")
def cache_info():
    return cache.info()


# ============================ CRYPTO =======================================
@app.get("/crypto/universe", tags=["crypto"], summary="Daftar universe koin")
def crypto_universe():
    syms = _guard(C.universe)
    return {"count": len(syms), "symbols": syms}


@app.get("/crypto/universe/{symbol}", tags=["crypto"], summary="Info satu koin")
def crypto_universe_one(symbol: str):
    d = _guard(C.universe_info, symbol.upper())
    if not d:
        raise HTTPException(404, f"symbol tidak ada di universe: {symbol}")
    return d


@app.get("/crypto/klines", tags=["crypto"], summary="OHLCV dari MEXC")
def crypto_klines(
    symbol: str = Query(..., examples=["BTCUSDT"]),
    interval: str = Query("1h", description="5m | 15m | 1h | 4h | 1d"),
    limit: int = Query(300, ge=10, le=2000),
):
    key = f"kl:{symbol.upper()}:{interval}:{limit}"
    return _guard(cache.cached, key, TTL["klines"],
                  lambda: C.klines(symbol, interval, limit))


@app.get("/crypto/ticker", tags=["crypto"], summary="Volume & harga 24H (Binance)")
def crypto_ticker(symbol: str = Query(..., examples=["BTCUSDT"])):
    key = f"tk:{symbol.upper()}"
    return _guard(cache.cached, key, TTL["ticker"], lambda: C.ticker(symbol))


@app.get("/crypto/funding", tags=["crypto"], summary="Funding rate + Open Interest")
def crypto_funding(symbol: str = Query(..., examples=["BTCUSDT"])):
    key = f"fd:{symbol.upper()}"
    return _guard(cache.cached, key, TTL["ticker"], lambda: C.funding(symbol))


@app.get("/crypto/sectors", tags=["crypto"], summary="Tren per sektor (MEXC)")
def crypto_sectors():
    return _guard(cache.cached, "sectors", TTL["sectors"], C.sectors)


@app.get("/crypto/sector/{symbol}", tags=["crypto"], summary="Sektor satu koin")
def crypto_sector_one(symbol: str):
    return _guard(C.sector_of, symbol)


@app.get("/crypto/news", tags=["crypto"], summary="Kalender berita ekonomi")
def crypto_news(
    days_ahead: int = Query(3, ge=0, le=14),
    min_impact: str = Query("High", description="High | Medium | Low"),
):
    key = f"nw:{days_ahead}:{min_impact}"
    return _guard(cache.cached, key, TTL["news"],
                  lambda: C.news(days_ahead, min_impact))


@app.get("/crypto/equity", tags=["crypto"], summary="Kurva equity & statistik")
def crypto_equity():
    return _guard(cache.cached, "equity", TTL["equity"], C.equity)


@app.get("/crypto/levels", tags=["crypto"], summary="Hitung SL/TP untuk satu koin")
def crypto_levels(
    symbol: str = Query(..., examples=["BTCUSDT"]),
    play: str = Query("scalping", description="scalping | intraday"),
    side: str = Query("LONG", description="LONG | SHORT"),
):
    if play not in ("scalping", "intraday"):
        raise HTTPException(400, "play harus 'scalping' atau 'intraday'")
    if side.upper() not in ("LONG", "SHORT"):
        raise HTTPException(400, "side harus 'LONG' atau 'SHORT'")
    key = f"lv:{symbol.upper()}:{play}:{side.upper()}"
    return _guard(cache.cached, key, TTL["levels"],
                  lambda: C.levels(symbol, play, side))


@app.get("/crypto/plays", tags=["crypto"], summary="Konfigurasi play crypto")
def crypto_plays():
    return _guard(C.plays_config)


# ============================ FOREX ========================================
@app.get("/forex/instruments", tags=["forex"], summary="Instrumen forex tersedia")
def forex_instruments():
    return F.instruments()


@app.get("/forex/klines", tags=["forex"], summary="OHLCV forex (TradingView)")
def forex_klines(
    symbol: str = Query(..., examples=["XAUUSD"]),
    interval: str = Query("60", description="5 | 15 | 60 | 240 | 1D | 1W"),
    limit: int = Query(200, ge=10, le=1000),
):
    key = f"fkl:{symbol.upper()}:{interval}:{limit}"
    return _guard(cache.cached, key, TTL["klines"],
                  lambda: F.klines(symbol, interval, limit))


@app.get("/forex/dxy", tags=["forex"], summary="Perubahan DXY")
def forex_dxy():
    return _guard(cache.cached, "dxy", TTL["ticker"], F.dxy_change)


@app.get("/forex/levels", tags=["forex"], summary="Hitung SL/TP forex")
def forex_levels(
    symbol: str = Query(..., examples=["XAUUSD"]),
    play: str = Query("scalping", description="scalping | intraday"),
    side: str = Query("LONG", description="LONG | SHORT"),
):
    if side.upper() not in ("LONG", "SHORT"):
        raise HTTPException(400, "side harus 'LONG' atau 'SHORT'")
    key = f"flv:{symbol.upper()}:{play}:{side.upper()}"
    return _guard(cache.cached, key, TTL["levels"],
                  lambda: F.levels(symbol, play, side))


@app.get("/forex/plays", tags=["forex"], summary="Konfigurasi play forex")
def forex_plays():
    return _guard(F.plays_config)
