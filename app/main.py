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
from . import sources_idx as I
from . import sources_journal as J
from . import sources_cron as K

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
            "forex_journal": ["/forex/journal/stats", "/forex/journal/trades",
                              "/forex/journal/watchlist", "/forex/journal/edge",
                              "/forex/journal/scanlog", "/forex/journal/performance",
                              "/forex/journal/session", "/forex/journal/multipair",
                              "/forex/journal/charts"],
            "idx": ["/idx/stats", "/idx/signals", "/idx/history/{job_id}",
                    "/idx/latest/{job_id}", "/idx/market", "/idx/flow",
                    "/idx/scanners", "/idx/news", "/idx/official",
                    "/idx/feed", "/idx/equity", "/idx/ledger"],
            "cron": ["/cron/jobs", "/cron/jobs/{job_id}", "/cron/executions",
                     "/cron/summary"],
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


# ============================ IDX (SAHAM) ==================================
@app.get("/idx/stats", tags=["idx"], summary="Statistik IDX")
def idx_stats():
    return _guard(cache.cached, "idx:stats", TTL["scan"], I.stats)


@app.get("/idx/signals", tags=["idx"], summary="Daftar sinyal IDX")
def idx_signals(
    preset: str | None = Query(None, description="filter preset"),
    limit: int = Query(100, ge=1, le=500),
):
    key = f"idx:sig:{preset}:{limit}"
    return _guard(cache.cached, key, TTL["scan"],
                  lambda: I.signals(preset, limit))


@app.get("/idx/history/{job_id}", tags=["idx"], summary="Riwayat sinyal per job")
def idx_history(job_id: str, limit: int = Query(20, ge=1, le=200)):
    key = f"idx:hist:{job_id}:{limit}"
    return _guard(cache.cached, key, TTL["scan"],
                  lambda: I.history(job_id, limit))


@app.get("/idx/latest/{job_id}", tags=["idx"], summary="Sinyal terakhir per job")
def idx_latest(job_id: str):
    key = f"idx:latest:{job_id}"
    return _guard(cache.cached, key, TTL["scan"], lambda: I.latest(job_id))


@app.get("/idx/market", tags=["idx"], summary="Data market IDX")
def idx_market(limit: int = Query(30, ge=1, le=200)):
    key = f"idx:mkt:{limit}"
    return _guard(cache.cached, key, TTL["scan"], lambda: I.market(limit))


@app.get("/idx/flow", tags=["idx"], summary="Aliran dana per ticker")
def idx_flow(
    ticker: str = Query(..., examples=["BBRI"]),
    days: int = Query(7, ge=1, le=90),
):
    key = f"idx:flow:{ticker.upper()}:{days}"
    return _guard(cache.cached, key, TTL["scan"],
                  lambda: I.flow(ticker, days))


@app.get("/idx/scanners", tags=["idx"], summary="Daftar scanner IDX")
def idx_scanners():
    return _guard(cache.cached, "idx:scan", TTL["scan"], I.scanners)


@app.get("/idx/news", tags=["idx"], summary="Berita IDX")
def idx_news():
    return _guard(cache.cached, "idx:news", TTL["news"], I.news)


@app.get("/idx/official", tags=["idx"], summary="Data resmi IDX")
def idx_official():
    return _guard(cache.cached, "idx:official", TTL["scan"], I.official)


@app.get("/idx/feed", tags=["idx"], summary="Feed sinyal ringkas")
def idx_feed(limit: int = Query(50, ge=1, le=200)):
    key = f"idx:feed:{limit}"
    return _guard(cache.cached, key, TTL["scan"], lambda: I.feed(limit))


@app.get("/idx/equity", tags=["idx"], summary="Kurva equity IDX")
def idx_equity():
    return _guard(cache.cached, "idx:equity", TTL["equity"], I.equity)


@app.get("/idx/ledger", tags=["idx"], summary="Metrik ledger sinyal IDX")
def idx_ledger():
    return _guard(cache.cached, "idx:ledger", TTL["scan"], I.ledger_metrics)


# ==================== FOREX JOURNAL (XAU / NAS100) =========================
@app.get("/forex/journal/stats", tags=["forex-journal"], summary="Statistik journal")
def journal_stats():
    return _guard(cache.cached, "j:stats", TTL["equity"], J.stats)


@app.get("/forex/journal/trades", tags=["forex-journal"], summary="Daftar trade journal")
def journal_trades(limit: int = Query(50, ge=1, le=500)):
    key = f"j:trades:{limit}"
    return _guard(cache.cached, key, TTL["equity"], lambda: J.trades(limit))


@app.get("/forex/journal/watchlist", tags=["forex-journal"], summary="Watchlist forex")
def journal_watchlist():
    return _guard(cache.cached, "j:wl", TTL["equity"], J.watchlist)


@app.get("/forex/journal/edge", tags=["forex-journal"], summary="Edge statistik")
def journal_edge():
    return _guard(cache.cached, "j:edge", TTL["equity"], J.edge)


@app.get("/forex/journal/scanlog", tags=["forex-journal"], summary="Log scan forex")
def journal_scanlog():
    return _guard(cache.cached, "j:scanlog", TTL["scan"], J.scanlog)


@app.get("/forex/journal/performance", tags=["forex-journal"], summary="Performa forex")
def journal_performance():
    return _guard(cache.cached, "j:perf", TTL["equity"], J.performance)


@app.get("/forex/journal/session", tags=["forex-journal"], summary="Sesi market")
def journal_session():
    return _guard(cache.cached, "j:sess", TTL["ticker"], J.session)


@app.get("/forex/journal/multipair", tags=["forex-journal"], summary="Multi-pair forex")
def journal_multipair():
    return _guard(cache.cached, "j:mp", TTL["scan"], J.multipair)


@app.get("/forex/journal/charts", tags=["forex-journal"], summary="Chart forex")
def journal_charts(limit: int = Query(8, ge=1, le=50)):
    key = f"j:charts:{limit}"
    return _guard(cache.cached, key, TTL["scan"], lambda: J.charts(limit))


# ============================ CRONJOBS =====================================
@app.get("/cron/jobs", tags=["cron"], summary="Daftar cronjob")
def cron_jobs():
    return _guard(cache.cached, "cron:jobs", 30, K.jobs)


@app.get("/cron/jobs/{job_id}", tags=["cron"], summary="Detail satu cronjob")
def cron_job(job_id: str):
    key = f"cron:job:{job_id}"
    return _guard(cache.cached, key, 30, lambda: K.job(job_id))


@app.get("/cron/executions", tags=["cron"], summary="Riwayat eksekusi cronjob")
def cron_executions(
    job_id: str | None = Query(None, description="filter job id"),
    limit: int = Query(50, ge=1, le=500),
):
    key = f"cron:exec:{job_id}:{limit}"
    return _guard(cache.cached, key, 30,
                  lambda: K.executions(job_id, limit))


@app.get("/cron/summary", tags=["cron"], summary="Ringkasan status cronjob")
def cron_summary():
    return _guard(cache.cached, "cron:summary", 30, K.summary)
