"""The move rule: what changed for the items of each source on a given day.

Move rule (also in the README, and mirrored in app.js for the website):
  * For each source that has rows on the day, its previous run is the latest
    earlier day on which that source has rows. A source with no earlier day is
    its first load, so nothing is compared.
  * An item that is in the day's rows but not in the previous run APPEARED.
    An item that is in the previous run but not in the day's rows is GONE.
  * For an item in both, the MOVE is the change in temp_c, new minus old,
    rounded to 2 decimals (degrees Celsius). Items with no temp_c on either
    day have no move.
  * Moves are ranked by absolute size, then by item_id.
"""
TOP = 5            # how many moves the daily issue lists
MOVE_COLUMN = "temp_c"


def num(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def compare(rows, date):
    by_source = {}
    for r in rows:
        by_source.setdefault(r["source"], {}).setdefault(r["date"], {})[r["item_id"]] = r
    moves, appeared, gone = [], [], []
    for source, days in sorted(by_source.items()):
        if date not in days:
            continue
        earlier = [d for d in days if d < date]
        if not earlier:
            continue
        cur, prev = days[date], days[max(earlier)]
        appeared += [cur[i] for i in sorted(cur) if i not in prev]
        gone += [prev[i] for i in sorted(prev) if i not in cur]
        for i in sorted(cur):
            if i in prev:
                new, old = num(cur[i].get(MOVE_COLUMN)), num(prev[i].get(MOVE_COLUMN))
                if new is not None and old is not None:
                    moves.append({"item_id": i, "item": cur[i]["item"], "source": source,
                                  "old": old, "new": new, "change": round(new - old, 2)})
    moves.sort(key=lambda m: (-abs(m["change"]), m["item_id"]))
    appeared.sort(key=lambda r: r["item_id"])
    gone.sort(key=lambda r: r["item_id"])
    return {"moves": moves, "appeared": appeared, "gone": gone}
