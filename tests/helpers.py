import gzip
import json

SOURCES = {
    "wa": {"name": "wa", "label": "A", "format": "json", "url": "https://x.test/a", "items": [
        {"id": "ann", "name": "Ann", "country": "United States", "region": "North America", "lat": 10.0, "lon": 10.0},
        {"id": "bay", "name": "Bay", "country": "United States", "region": "North America", "lat": 20.0, "lon": 20.0}]},
    "wb": {"name": "wb", "label": "B", "format": "json", "url": "https://x.test/b", "items": [
        {"id": "cove", "name": "Cove", "country": "France", "region": "Europe", "lat": 40.0, "lon": 40.0},
        {"id": "dune", "name": "Dune", "country": "Japan", "region": "Asia", "lat": 50.0, "lon": 50.0}]},
}


def om(src, temps, **extra):
    """An Open-Meteo style list for a source: one result per item, in order.

    Coordinates are nudged (the API snaps to a grid), so matching must be by nearest city.
    """
    out = []
    for item, t in zip(src["items"], temps):
        cur = {"time": "2026-01-01T06:00", "temperature_2m": t, "apparent_temperature": t - 1,
               "relative_humidity_2m": 60, "wind_speed_10m": 10.5, "surface_pressure": 1013.2}
        cur.update(extra)
        out.append({"latitude": item["lat"] + 0.04, "longitude": item["lon"] - 0.03, "current": cur})
    return out


def write_raw(raw_dir, date, source, raw):
    d = raw_dir / date
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{source}.json.gz").write_bytes(gzip.compress(json.dumps(raw).encode()))
