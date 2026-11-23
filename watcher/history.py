"""Build data/history.csv from the raw files alone.

The build is a pure function of data/raw/<date>/<source>.json.gz and
sources.json: running it again gives the same file, and a change to a rule
applies to every day of the history.

Command:  python -m watcher.history
"""
import csv
import gzip
import json
from pathlib import Path

from . import convert

ROOT = Path(__file__).resolve().parent.parent
SUFFIX = ".json.gz"


def raw_files(raw_dir):
    """Return {date: {source: path}} for every raw file under raw_dir."""
    days = {}
    for path in sorted(Path(raw_dir).glob("*/*" + SUFFIX)):
        days.setdefault(path.parent.name, {})[path.name[: -len(SUFFIX)]] = path
    return days


def read_raw(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def build_history(raw_dir, sources):
    """One row per item per day, sorted by date then item_id."""
    days = raw_files(raw_dir)
    rows = []
    for date in sorted(days):
        seen = set()
        for source in sorted(days[date]):
            if source not in sources:
                continue
            for r in convert.convert(sources[source], read_raw(days[date][source])):
                if r["item_id"] in seen:
                    continue
                seen.add(r["item_id"])
                rows.append(dict(r, date=date))
    return sorted(rows, key=lambda r: (r["date"], r["item_id"]))


def write_history(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(convert.HISTORY_COLUMNS)
        for r in rows:
            w.writerow(["" if r.get(c) is None else r[c] for c in convert.HISTORY_COLUMNS])


def read_history(path):
    """Read history.csv back into rows (numbers stay as text)."""
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    sources = convert.load_sources(ROOT / "sources.json")
    rows = build_history(ROOT / "data" / "raw", sources)
    write_history(rows, ROOT / "data" / "history.csv")
    print(f"wrote data/history.csv with {len(rows)} rows")


if __name__ == "__main__":
    main()
