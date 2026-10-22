"""Sumber data cronjob — read-only.

Membaca definisi job dan riwayat eksekusi. Tidak membuat/mengubah job.
"""
import json
import os
import sqlite3
from pathlib import Path

HERMES = Path(os.environ.get("HERMES_HOME", "/home/ubuntu/.hermes"))
JOBS = HERMES / "cron" / "jobs.json"
EXEC_DB = HERMES / "cron" / "executions.db"


def jobs() -> dict:
    if not JOBS.exists():
        raise LookupError("jobs.json tidak ditemukan")
    data = json.loads(JOBS.read_text())
    out = []
    for j in data.get("jobs", []):
        out.append({
            "id": j.get("id"),
            "name": j.get("name"),
            "schedule": j.get("schedule"),
            "enabled": j.get("enabled", True),
            "script": j.get("script"),
            "deliver": j.get("deliver"),
            "next_run": j.get("next_run"),
            "last_run": j.get("last_run"),
            "last_status": j.get("last_status"),
        })
    return {"count": len(out), "jobs": out}


def job(job_id: str) -> dict:
    if not JOBS.exists():
        raise LookupError("jobs.json tidak ditemukan")
    data = json.loads(JOBS.read_text())
    for j in data.get("jobs", []):
        if j.get("id") == job_id or j.get("name") == job_id:
            return j
    raise LookupError(f"job tidak ditemukan: {job_id}")


def executions(job_id: str | None = None, limit: int = 50) -> dict:
    if not EXEC_DB.exists():
        raise LookupError("executions.db tidak ditemukan")
    con = sqlite3.connect(f"file:{EXEC_DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        cols = [r["name"] for r in con.execute("PRAGMA table_info(executions)")]
        if not cols:
            raise LookupError("tabel executions tidak ada")
        sql = "SELECT * FROM executions"
        args = []
        if job_id and "job_id" in cols:
            sql += " WHERE job_id = ?"
            args.append(job_id)
        order = " ORDER BY rowid DESC LIMIT ?"
        sql += order
        args.append(limit)
        rows = [dict(r) for r in con.execute(sql, args)]
        return {"count": len(rows), "columns": cols, "executions": rows}
    finally:
        con.close()


def summary() -> dict:
    """Ringkasan status semua job: berapa aktif, terakhir sukses/gagal."""
    j = jobs()
    items = j["jobs"]
    active = sum(1 for x in items if x.get("enabled"))
    ok = sum(1 for x in items if str(x.get("last_status") or "").lower() == "ok")
    fail = sum(1 for x in items if str(x.get("last_status") or "").lower() not in ("", "ok", "none"))
    return {
        "total": len(items),
        "enabled": active,
        "disabled": len(items) - active,
        "last_ok": ok,
        "last_failed": fail,
        "jobs": items,
    }
