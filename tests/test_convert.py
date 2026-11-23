import pytest

from watcher import convert
from tests.helpers import SOURCES, om


def test_converts_each_source_to_common_columns():
    for name, temps in (("wa", [11.5, 22.0]), ("wb", [5.0, 31.2])):
        src = SOURCES[name]
        rows = convert.convert(src, om(src, temps))
        assert [r["item_id"] for r in rows] == [i["id"] for i in src["items"]]
        r = rows[0]
        assert r["item"] == src["items"][0]["name"] and r["source"] == name
        assert r["country"] == src["items"][0]["country"] and r["region"] == src["items"][0]["region"]
        assert r["temp_c"] == temps[0] and r["feels_like_c"] == temps[0] - 1
        assert (r["humidity_pct"], r["wind_kmh"], r["pressure_hpa"]) == (60, 10.5, 1013.2)


def test_matches_by_nearest_city_not_by_order():
    src = SOURCES["wa"]
    rows = convert.convert(src, list(reversed(om(src, [11.5, 22.0]))))
    assert {r["item_id"]: r["temp_c"] for r in rows} == {"ann": 11.5, "bay": 22.0}


def test_missing_value_is_none():
    src = SOURCES["wa"]
    raw = om(src, [11.5, 22.0])
    del raw[0]["current"]["wind_speed_10m"]
    raw[1]["current"]["surface_pressure"] = None
    rows = convert.convert(src, raw)
    assert rows[0]["wind_kmh"] is None and rows[1]["pressure_hpa"] is None


def test_single_result_object_is_accepted():
    src = SOURCES["wa"]
    assert len(convert.convert(src, om(src, [1.0, 2.0])[0])) == 1


@pytest.mark.parametrize("raw", [[], "oops", {"error": True}, [{"latitude": 1, "longitude": 1}]])
def test_unexpected_shape_raises(raw):
    with pytest.raises(ValueError):
        convert.convert(SOURCES["wa"], raw)


def test_result_far_from_every_city_raises():
    raw = [{"latitude": 80.0, "longitude": 80.0, "current": {"temperature_2m": 1}}]
    with pytest.raises(ValueError):
        convert.convert(SOURCES["wa"], raw)


def test_request_params_cover_every_city():
    p = convert.request_params(SOURCES["wa"])
    assert p["latitude"] == "10.0,20.0" and p["longitude"] == "10.0,20.0"
    assert "temperature_2m" in p["current"]
