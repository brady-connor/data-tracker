import csv
from datetime import datetime, timezone

from watcher import convert, history, status
from tests.helpers import SOURCES, om, write_raw

D1, D2, D3 = "2026-01-01", "2026-01-02", "2026-01-03"
A, B = SOURCES["wa"], SOURCES["wb"]


def test_one_row_per_item_per_day_sorted_by_date_then_item_id(tmp_path):
    write_raw(tmp_path, D2, "wb", om(B, [1.0, 2.0]))
    write_raw(tmp_path, D1, "wb", om(B, [3.0, 4.0]))
    write_raw(tmp_path, D1, "wa", om(A, [5.0, 6.0]))
    rows = history.build_history(tmp_path, SOURCES)
    keys = [(r["date"], r["item_id"]) for r in rows]
    assert keys == sorted(keys) and len(keys) == len(set(keys)) == 6
    assert keys[0] == (D1, "ann")


def test_day_without_a_raw_file_has_no_rows_from_that_source(tmp_path):
    write_raw(tmp_path, D1, "wa", om(A, [1.0, 2.0]))
    write_raw(tmp_path, D1, "wb", om(B, [1.0, 2.0]))
    write_raw(tmp_path, D2, "wb", om(B, [1.0, 2.0]))      # wa failed on D2
    rows = history.build_history(tmp_path, SOURCES)
    assert [r["source"] for r in rows if r["date"] == D2] == ["wb", "wb"]


def test_unknown_source_files_are_ignored(tmp_path):
    write_raw(tmp_path, D1, "old-source", om(A, [1.0, 2.0]))
    assert history.build_history(tmp_path, SOURCES) == []


def test_empty_value_is_left_empty_in_the_csv(tmp_path):
    raw = om(A, [1.0, 2.0])
    del raw[0]["current"]["wind_speed_10m"]
    write_raw(tmp_path, D1, "wa", raw)
    history.write_history(history.build_history(tmp_path, SOURCES), tmp_path / "h.csv")
    rows = list(csv.DictReader(open(tmp_path / "h.csv", newline="")))
    assert rows[0]["wind_kmh"] == "" and rows[1]["wind_kmh"] == "10.5"
    assert list(rows[0])[:4] == ["date", "item_id", "item", "source"]


def test_build_is_reproducible_from_the_raw_files(tmp_path):
    write_raw(tmp_path, D1, "wa", om(A, [1.0, 2.0]))
    write_raw(tmp_path, D2, "wa", om(A, [3.0, 4.0]))
    history.write_history(history.build_history(tmp_path, SOURCES), tmp_path / "a.csv")
    history.write_history(history.build_history(tmp_path, SOURCES), tmp_path / "b.csv")
    assert (tmp_path / "a.csv").read_bytes() == (tmp_path / "b.csv").read_bytes()


def test_a_rule_change_applies_to_every_day(tmp_path):
    write_raw(tmp_path, D1, "wa", om(A, [1.0, 2.0]))
    write_raw(tmp_path, D2, "wa", om(A, [3.0, 4.0]))
    renamed = {"wa": dict(A, items=[dict(A["items"][0], name="Annie"), A["items"][1]])}
    rows = history.build_history(tmp_path, renamed)
    assert [r["item"] for r in rows if r["item_id"] == "ann"] == ["Annie", "Annie"]


def test_status_counts(tmp_path):
    write_raw(tmp_path, D1, "wa", om(A, [1.0, 2.0]))
    write_raw(tmp_path, D2, "wa", om(A, [3.0]))             # "bay" is no longer reported
    rows = history.build_history(tmp_path, SOURCES)
    results = [{"name": "wa", "ok": True, "count": 1}, {"name": "wb", "ok": False, "count": 0}]
    st = status.build_status(rows, results, datetime(2026, 1, 2, 6, 0, tzinfo=timezone.utc), D2, tmp_path)
    assert st["first_run_date"] == D1 and st["days_with_success"] == 2
    assert st["items"] == 1 and st["gone_today"] == 1 and st["new_today"] == 0
    assert st["run_time"] == "2026-01-02T06:00:00Z" and st["sources"][1] == {"name": "wb", "ok": False, "count": 0}
    assert set(st) == {"run_time", "first_run_date", "days_with_success", "items",
                       "new_today", "gone_today", "sources"}
