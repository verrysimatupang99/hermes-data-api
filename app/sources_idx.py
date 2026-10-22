"""Sumber data IDX (saham Indonesia) — read-only.

Membaca dari database & file yang sudah dipakai dashboard IDX.
"""
import sys

from .config import SCRIPTS

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def stats() -> dict:
    import idx_dashboard_api as A
    return A.api_stats()


def signals(preset: str | None = None, limit: int = 100) -> dict:
    import idx_dashboard_api as A
    rows = A.api_signals(preset=preset, limit=limit)
    return {"count": len(rows), "signals": rows}


def history(job_id: str, limit: int = 20) -> dict:
    import idx_dashboard_api as A
    rows = A.api_history(job_id, limit=limit)
    return {"job_id": job_id, "count": len(rows), "history": rows}


def latest(job_id: str) -> dict:
    import idx_dashboard_api as A
    return A.api_latest(job_id)


def market(limit: int = 30) -> dict:
    import idx_dashboard_api as A
    rows = A.api_market(limit=limit)
    return {"count": len(rows), "market": rows}


def flow(ticker: str, days: int = 7) -> dict:
    import idx_dashboard_api as A
    return A.api_flow(ticker, days=days)


def scanners() -> dict:
    import idx_dashboard_api as A
    return A.api_scanners()


def news() -> dict:
    import idx_dashboard_api as A
    return A.api_news()


def official() -> dict:
    import idx_dashboard_api as A
    return A.api_official()


def feed(limit: int = 50) -> dict:
    """Feed sinyal ringkas dari idx616_feed."""
    import idx616_feed as F
    return F.signals(limit=limit)


def equity() -> dict:
    """Kurva equity IDX."""
    import idx616_feed as F
    return F.equity()


def ledger_metrics() -> dict:
    """Metrik dari ledger sinyal IDX."""
    import idx616_ledger as L
    return L.metrics()
