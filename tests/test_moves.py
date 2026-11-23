from watcher import moves


def row(date, item_id, temp, source="s"):
    return {"date": date, "item_id": item_id, "item": item_id.title(), "source": source, "temp_c": temp}


D1, D2, D3 = "2026-01-01", "2026-01-02", "2026-01-03"


def test_move_is_new_minus_old_rounded_and_ranked_by_size():
    rows = [row(D1, "a", 10.0), row(D1, "b", 20.0), row(D1, "c", 5.0),
            row(D2, "a", 10.3), row(D2, "b", 17.5), row(D2, "c", 5.0)]
    ch = moves.compare(rows, D2)
    assert [(m["item_id"], m["change"]) for m in ch["moves"]] == [("b", -2.5), ("a", 0.3), ("c", 0.0)]
    assert ch["moves"][0]["old"] == 20.0 and ch["moves"][0]["new"] == 17.5


def test_float_noise_is_rounded_and_ties_break_by_item_id():
    rows = [row(D1, "b", 11.1), row(D1, "a", 11.1), row(D2, "b", 12.3), row(D2, "a", 12.3)]
    ch = moves.compare(rows, D2)
    assert [(m["item_id"], m["change"]) for m in ch["moves"]] == [("a", 1.2), ("b", 1.2)]


def test_appeared_and_gone():
    rows = [row(D1, "a", 1.0), row(D1, "b", 2.0), row(D2, "a", 1.0), row(D2, "c", 3.0)]
    ch = moves.compare(rows, D2)
    assert [r["item_id"] for r in ch["appeared"]] == ["c"]
    assert [r["item_id"] for r in ch["gone"]] == ["b"]
    assert [m["item_id"] for m in ch["moves"]] == ["a"]


def test_first_load_of_a_source_compares_nothing():
    ch = moves.compare([row(D1, "a", 1.0), row(D1, "b", 2.0)], D1)
    assert ch == {"moves": [], "appeared": [], "gone": []}


def test_source_without_rows_today_is_not_reported_gone():
    rows = [row(D1, "a", 1.0, "s1"), row(D1, "x", 1.0, "s2"),
            row(D2, "a", 2.0, "s1")]                      # s2 failed on D2
    ch = moves.compare(rows, D2)
    assert ch["gone"] == [] and [m["item_id"] for m in ch["moves"]] == ["a"]


def test_compares_with_the_sources_previous_run_even_after_a_gap():
    rows = [row(D1, "a", 10.0), row(D3, "a", 14.0)]       # no rows on D2
    ch = moves.compare(rows, D3)
    assert ch["moves"][0]["old"] == 10.0 and ch["moves"][0]["change"] == 4.0


def test_missing_temperature_has_no_move_and_text_numbers_work():
    rows = [row(D1, "a", ""), row(D2, "a", "5"), row(D1, "b", "2.5"), row(D2, "b", "4")]
    ch = moves.compare(rows, D2)
    assert [(m["item_id"], m["change"]) for m in ch["moves"]] == [("b", 1.5)]
