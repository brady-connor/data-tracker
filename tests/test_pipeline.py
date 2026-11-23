import json

from watcher import history, pipeline
from tests.helpers import SOURCES, om


class Resp:
    def __init__(self, data):
        self.text = json.dumps(data)

    def raise_for_status(self):
        pass


class FakeSession:
    """Returns data per source, chosen by the request's latitude list."""
    def __init__(self, by_source):
        self.by_source = by_source

    def get(self, url, params=None, **kw):
        for name, src in SOURCES.items():
            if params["latitude"] == ",".join(str(i["lat"]) for i in src["items"]):
                data = self.by_source[name]
                if isinstance(data, Exception):
                    raise data
                return Resp(data)
        raise RuntimeError("unknown request")


def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline.time, "sleep", lambda s: None)
    (tmp_path / "sources.json").write_text(json.dumps(list(SOURCES.values())))


def good(ta, tb):
    return {"wa": om(SOURCES["wa"], ta), "wb": om(SOURCES["wb"], tb)}


def test_failed_source_writes_no_file_and_run_continues(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    session = FakeSession({"wa": om(SOURCES["wa"], [1.0, 2.0]), "wb": RuntimeError("boom")})
    st, results = pipeline.run("2026-01-01", root=tmp_path, session=session)
    day = tmp_path / "data" / "raw" / "2026-01-01"
    assert (day / "wa.json.gz").exists() and not (day / "wb.json.gz").exists()
    assert [(r["name"], r["ok"], r["count"]) for r in results] == [("wa", True, 2), ("wb", False, 0)]
    assert st["items"] == 2 and st["days_with_success"] == 1
    assert (tmp_path / "data" / "history.csv").exists() and (tmp_path / "data" / "status.json").exists()


def test_bad_response_counts_as_a_failure(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    session = FakeSession({"wa": {"error": True}, "wb": om(SOURCES["wb"], [1.0, 2.0])})
    _, results = pipeline.run("2026-01-01", root=tmp_path, session=session)
    assert results[0]["ok"] is False and results[1]["ok"] is True
    assert not (tmp_path / "data" / "raw" / "2026-01-01" / "wa.json.gz").exists()


def test_second_run_on_the_same_day_replaces_the_day(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    pipeline.run("2026-01-01", root=tmp_path, session=FakeSession(good([1.0, 2.0], [3.0, 4.0])))
    st, _ = pipeline.run("2026-01-01", root=tmp_path,
                         session=FakeSession({"wa": om(SOURCES["wa"], [9.0, 9.5]), "wb": RuntimeError("x")}))
    day = tmp_path / "data" / "raw" / "2026-01-01"
    assert sorted(p.name for p in day.glob("*.json.gz")) == ["wa.json.gz"]
    assert st["days_with_success"] == 1 and st["items"] == 2
    rows = history.read_history(tmp_path / "data" / "history.csv")
    assert len(rows) == 2 and {r["temp_c"] for r in rows} == {"9.0", "9.5"}   # counted once, replaced


def test_rerun_rebuilds_the_same_history_file(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    pipeline.run("2026-01-01", root=tmp_path, session=FakeSession(good([1.0, 2.0], [3.0, 4.0])))
    pipeline.run("2026-01-02", root=tmp_path, session=FakeSession(good([2.0, 2.5], [3.0, 4.5])))
    first = (tmp_path / "data" / "history.csv").read_bytes()
    monkeypatch.setattr(history, "ROOT", tmp_path)   # the build command, pointed at this repo
    history.main()
    assert (tmp_path / "data" / "history.csv").read_bytes() == first


def test_issue_lists_moves_with_old_and_new_values(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    pipeline.run("2026-01-01", root=tmp_path, session=FakeSession(good([10.0, 20.0], [5.0, 6.0])))
    st, _ = pipeline.run("2026-01-02", root=tmp_path, session=FakeSession(good([10.5, 15.0], [5.0, 6.0])))
    body = (tmp_path / "issue_body.md").read_text()
    assert "| Bay | 20 | 15 | -5 |" in body and "Ann" in body
    assert body.index("Bay") < body.index("Ann")       # biggest move first
    assert st["new_today"] == 0 and st["gone_today"] == 0 and st["days_with_success"] == 2
