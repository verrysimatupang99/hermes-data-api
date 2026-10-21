"""Cache in-memory sederhana dengan TTL. Read-only, tanpa disk."""
import time
from typing import Any, Callable

_store: dict[str, tuple[float, Any]] = {}


def cached(key: str, ttl: int, fn: Callable[[], Any]) -> Any:
    """Ambil dari cache kalau masih segar, kalau tidak panggil fn()."""
    now = time.time()
    hit = _store.get(key)
    if hit and (now - hit[0]) < ttl:
        return hit[1]
    val = fn()
    _store[key] = (now, val)
    return val


def clear() -> int:
    n = len(_store)
    _store.clear()
    return n


def info() -> dict:
    now = time.time()
    return {
        "entries": len(_store),
        "keys": [
            {"key": k, "age_s": round(now - ts, 1)}
            for k, (ts, _) in sorted(_store.items())
        ],
    }
