"""Build the contents of data/status.json for the latest run."""
from . import history, moves


def build_status(rows, results, now, date, raw_dir):
    days = sorted(history.raw_files(raw_dir))
    change = moves.compare(rows, date)
    return {
        "run_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "first_run_date": days[0] if days else "",
        "days_with_success": len(days),
        "items": sum(1 for r in rows if r["date"] == date),
        "new_today": len(change["appeared"]),
        "gone_today": len(change["gone"]),
        "sources": [
            {"name": s["name"], "ok": bool(s["ok"]), "count": int(s["count"])}
            for s in results
        ],
    }
