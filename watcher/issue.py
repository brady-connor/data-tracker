"""Daily GitHub Issue: build the body, then open/update today's and close old ones.

Run by the workflow after the pipeline:  python -m watcher.issue
"""
import json
import subprocess
from pathlib import Path

from . import moves

ROOT = Path(__file__).resolve().parent.parent


def build_body(rows, date):
    change = moves.compare(rows, date)
    top = change["moves"][: moves.TOP]
    lines = [f"Weather moves for {date} (UTC). A move is the change in temperature (deg C) "
             f"since the previous run; the {moves.TOP} biggest are listed.", ""]
    lines += [f"## Biggest moves ({len(top)} of {len(change['moves'])})", ""]
    if top:
        lines += ["| Item | Old (C) | New (C) | Change (C) |", "|---|---|---|---|"]
        lines += [f"| {m['item']} | {m['old']:g} | {m['new']:g} | {m['change']:+g} |" for m in top]
    else:
        lines += ["None (no earlier run to compare with)."]
    lines += ["", f"## Appeared ({len(change['appeared'])})", ""]
    lines += [f"- {r['item']} ({r['source']})" for r in change["appeared"]] or ["None."]
    lines += ["", f"## Disappeared ({len(change['gone'])})", ""]
    lines += [f"- {r['item']} ({r['source']})" for r in change["gone"]] or ["None."]
    return "\n".join(lines) + "\n"


def _gh(*args):
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def publish(date, body_path):
    _gh("label", "create", "data-tracker", "--color", "0f766e", "--force")
    existing = json.loads(_gh("issue", "list", "--state", "all", "--label", "data-tracker",
                              "--limit", "300", "--json", "number,title,state"))
    today = [i for i in existing if i["title"] == date]
    if today:
        number = str(today[0]["number"])
        _gh("issue", "edit", number, "--body-file", str(body_path))
        if today[0]["state"] != "OPEN":
            _gh("issue", "reopen", number)
    else:
        _gh("issue", "create", "--title", date, "--body-file", str(body_path),
            "--label", "data-tracker")
    for i in existing:
        if i["state"] == "OPEN" and i["title"] != date:
            _gh("issue", "close", str(i["number"]))


def main():
    status = json.loads((ROOT / "data" / "status.json").read_text())
    publish(status["run_time"][:10], ROOT / "issue_body.md")


if __name__ == "__main__":
    main()
