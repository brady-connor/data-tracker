"""Convert an Open-Meteo response to the common columns (one row per item)."""
import json

# Columns of data/history.csv. The first four are fixed by the assignment.
HISTORY_COLUMNS = [
    "date", "item_id", "item", "source",          # fixed
    "country", "region",                           # categories
    "temp_c", "feels_like_c", "humidity_pct", "wind_kmh", "pressure_hpa",  # numbers
]
NUMERIC = ["temp_c", "feels_like_c", "humidity_pct", "wind_kmh", "pressure_hpa"]

# Open-Meteo "current" variable -> our column
CURRENT = {
    "temperature_2m": "temp_c",
    "apparent_temperature": "feels_like_c",
    "relative_humidity_2m": "humidity_pct",
    "wind_speed_10m": "wind_kmh",
    "surface_pressure": "pressure_hpa",
}
MAX_DEGREES = 1.0   # a result must be this close to one of our cities


def load_sources(path):
    """Return {source name: source dict} from sources.json, in file order."""
    with open(path, encoding="utf-8") as f:
        return {s["name"]: s for s in json.load(f)}


def request_params(src):
    """Query string parameters for one source (one request covers all its cities)."""
    return {
        "latitude": ",".join(str(i["lat"]) for i in src["items"]),
        "longitude": ",".join(str(i["lon"]) for i in src["items"]),
        "current": ",".join(CURRENT),
        "timezone": "UTC",
    }


def _number(v):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return v


def _nearest(src, lat, lon):
    best, best_d = None, None
    for item in src["items"]:
        d = abs(item["lat"] - lat) + abs(item["lon"] - lon)
        if best_d is None or d < best_d:
            best, best_d = item, d
    if best is None or abs(best["lat"] - lat) > MAX_DEGREES or abs(best["lon"] - lon) > MAX_DEGREES:
        raise ValueError(f"result at {lat},{lon} matches no tracked city")
    return best


def convert(src, raw):
    """Rows (without the date) for one source. Raises ValueError on a bad response.

    Open-Meteo moves each result to a nearby grid point, so a result is matched
    to the closest tracked city instead of by exact coordinates.
    """
    results = [raw] if isinstance(raw, dict) else raw
    if not isinstance(results, list) or not results:
        raise ValueError("unexpected Open-Meteo response")
    rows, seen = [], set()
    for res in results:
        if not isinstance(res, dict) or not isinstance(res.get("current"), dict):
            raise ValueError("result has no current values")
        item = _nearest(src, res["latitude"], res["longitude"])
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        row = {"item_id": item["id"], "item": item["name"], "source": src["name"],
               "country": item["country"], "region": item["region"]}
        for var, col in CURRENT.items():
            row[col] = _number(res["current"].get(var))
        rows.append(row)
    return rows
