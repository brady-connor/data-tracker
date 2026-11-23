"""Daily pipeline: fetch sources -> raw files -> history -> status -> issue body.

    python -m watcher.pipeline            full run (what the daily workflow does)
    python -m watcher.pipeline --check    test every source, write nothing
"""
import argparse
import datetime as dt
import gzip
import json
import shutil
import time
from pathlib import Path

import requests

from . import convert, history, issue, status as status_mod

ROOT = Path(__file__).resolve().parent.parent
HEADERS = {"User-Agent": "data-tracker-class-project"}


def fetch(src, session, tries=3):
    """Download one source and return the response text."""
    last = None
    for attempt in range(tries):
        try:
            r = session.get(src["url"], params=convert.request_params(src),
                            timeout=60, headers=HEADERS)
            r.raise_for_status()
            return r.text
        except Exception as e:  # network error or HTTP error
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def run(date=None, root=ROOT, session=None, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    date = date or now.strftime("%Y-%m-%d")
    session = session or requests.Session()
    root = Path(root)
    sources = convert.load_sources(root / "sources.json")
    raw_dir = root / "data" / "raw"
    day_dir = raw_dir / date
    if day_dir.exists():                      # a second run replaces the day
        shutil.rmtree(day_dir)
    day_dir.mkdir(parents=True)

    results = []
    for name, src in sources.items():
        try:
            text = fetch(src, session)
            count = len(convert.convert(src, json.loads(text)))   # validates the response
            (day_dir / f"{name}.json.gz").write_bytes(gzip.compress(text.encode("utf-8"), mtime=0))
            results.append({"name": name, "ok": True, "count": count})
        except Exception as e:                 # one failing source must not stop the run
            results.append({"name": name, "ok": False, "count": 0, "error": str(e)[:200]})
    (day_dir / "_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")

    rows = history.build_history(raw_dir, sources)
    history.write_history(rows, root / "data" / "history.csv")
    st = status_mod.build_status(rows, results, now, date, raw_dir)
    (root / "data" / "status.json").write_text(json.dumps(st, indent=2) + "\n")
    (root / "issue_body.md").write_text(issue.build_body(rows, date), encoding="utf-8")
    return st, results


def check(root=ROOT):
    sources = convert.load_sources(Path(root) / "sources.json")
    session = requests.Session()
    bad = 0
    for name, src in sources.items():
        try:
            rows = convert.convert(src, json.loads(fetch(src, session, tries=1)))
            sample = rows[0]
            print(f"ok    {name:<14} {len(rows)} items, e.g. {sample['item']} {sample['temp_c']} C")
        except Exception as e:
            bad += 1
            print(f"FAIL  {name:<14} {str(e)[:80]}")
    print(f"{len(sources) - bad} of {len(sources)} sources work")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="test sources, write nothing")
    args = ap.parse_args()
    if args.check:
        check()
        return
    st, results = run()
    for s in results:
        print(("ok    " if s["ok"] else "FAIL  ") + f"{s['name']:<14} {s['count']} {s.get('error', '')}")
    print(json.dumps({k: v for k, v in st.items() if k != "sources"}))


if __name__ == "__main__":
    main()
