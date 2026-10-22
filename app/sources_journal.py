"""Sumber data journal forex (XAUUSD/NAS100) — read-only.

Membaca dari modul dashboard XAU yang sudah ada. Tidak mengubah state.
"""
import sys

from .config import SCRIPTS

if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def stats() -> dict:
    import xauusd_dashboard_api as A
    return A.api_stats()


def trades(limit: int = 50) -> dict:
    import xauusd_dashboard_api as A
    rows = A.api_trades(limit=limit)
    if isinstance(rows, dict):
        return rows
    return {"count": len(rows), "trades": rows}


def watchlist() -> dict:
    import xauusd_dashboard_api as A
    return A.api_watchlist()


def edge() -> dict:
    import xauusd_dashboard_api as A
    return A.api_edge()


def scanlog() -> dict:
    import xauusd_dashboard_api as A
    return A.api_scanlog()


def performance() -> dict:
    import xauusd_dashboard_api as A
    return A.api_performance()


def session() -> dict:
    import xauusd_dashboard_api as A
    return A.api_session()


def multipair() -> dict:
    import xauusd_dashboard_api as A
    return A.api_multipair()


def charts(limit: int = 8) -> dict:
    import xauusd_dashboard_api as A
    return A.api_charts(limit=limit)
