import csv
import json
from datetime import date

import pytest

from agents import paths, validate

TODAY = date(2026, 11, 11)
W = " ".join(["w"] * 600)


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUT_ROOT", tmp_path / "out")
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path / "data")
    f = tmp_path / "data" / "filings"
    f.mkdir(parents=True)
    m = [{"ticker": "AAA", "form": x, "filing_date": "2026-09-01", "file": "x", "title": "t", "url": "u"} for x in ("10-K", "10-Q")]
    (f / "manifest.json").write_text(json.dumps(m))
    od = paths.out_dir("AAA")
    write(od / "quote.csv", ["ticker", "price", "change", "change_pct", "currency", "as_of"], [["AAA", "10", "1", "1", "USD", "2026-11-10"]])
    write(od / "filings.csv", ["ticker", "form", "filing_date", "accession", "url"],
          [["AAA", "10-Q", "2026-09-01", "a", "u"], ["AAA", "10-K", "2026-06-01", "b", "u"]])
    return tmp_path


def write(p, head, rows):
    with p.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)


def make_ex(names=paths.REQUIRED_SECTIONS, body=W):
    ex = {}
    sd = paths.sections_dir("AAA")
    for n in names:
        p = sd / f"{n}.md"
        p.write_text(f"Source: t (u)\n\n{body}\n")
        ex[n] = {"ok": True, "detail": "ok", "path": str(p), "words": 600}
    return ex


def by_name(r):
    return {c["name"]: c for c in r["checks"]}


def test_pass(env):
    r = validate.run_checks("AAA", make_ex(), TODAY)
    assert r["passed"], r


def test_no_10q_in_manifest(env):
    (env / "data/filings/manifest.json").write_text("[]")
    assert not by_name(validate.run_checks("AAA", make_ex(), TODAY))["corpus_has_filings"]["ok"]


def test_stale_10q(env):
    write(paths.out_dir("AAA") / "filings.csv", ["ticker", "form", "filing_date", "accession", "url"],
          [["AAA", "10-Q", "2026-01-01", "a", "u"], ["AAA", "10-K", "2026-06-01", "b", "u"]])
    assert not by_name(validate.run_checks("AAA", make_ex(), TODAY))["filing_10q_recent"]["ok"]


def test_short_section_and_detail(env):
    ex = make_ex()
    ex["mdna"] = {"ok": False, "detail": "heading found but body under 200 words", "path": None, "words": 0}
    c = by_name(validate.run_checks("AAA", ex, TODAY))["sections_present"]
    assert not c["ok"] and "under 200" in c["detail"]
    assert not by_name(validate.run_checks("AAA", make_ex(body="few words"), TODAY))["sections_present"]["ok"]


def test_missing_mdna_10q_still_passes(env):
    ex = make_ex()
    ex["mdna_10q"] = {"ok": False, "detail": "heading not found", "path": None, "words": 0}
    assert validate.run_checks("AAA", ex, TODAY)["passed"]


@pytest.mark.parametrize("txt", ["Access Denied", "Page not found", "Error 404", "404 Not Found", "Request blocked"])
def test_error_pages(env, txt):
    r = validate.run_checks("AAA", make_ex(body=f"{W} {txt}"), TODAY)
    assert not by_name(r)["no_error_pages"]["ok"]


def test_dollar_404_million_ok(env):
    r = validate.run_checks("AAA", make_ex(body=f"{W} revenue was $404 million"), TODAY)
    assert by_name(r)["no_error_pages"]["ok"]


def test_bad_quote(env):
    od = paths.out_dir("AAA")
    h = ["ticker", "price", "change", "change_pct", "currency", "as_of"]
    write(od / "quote.csv", h, [["AAA", "abc", "1", "1", "USD", "2026-11-10"]])
    assert not by_name(validate.run_checks("AAA", make_ex(), TODAY))["quote_valid"]["ok"]
    write(od / "quote.csv", h, [["AAA", "10", "1", "1", "USD", "2026-10-01"]])
    assert not by_name(validate.run_checks("AAA", make_ex(), TODAY))["quote_valid"]["ok"]


def test_missing_csvs_do_not_raise(env):
    (paths.out_dir("AAA") / "quote.csv").unlink()
    (paths.out_dir("AAA") / "filings.csv").unlink()
    r = validate.run_checks("AAA", make_ex(), TODAY)
    assert not r["passed"]


def test_node_writes_json_and_paths(env):
    res = validate.validate("AAA")
    assert isinstance(res["paths"], list) and all(isinstance(p, str) for p in res["paths"])
    assert json.loads((paths.out_dir("AAA") / "validation.json").read_text())["ticker"] == "AAA"
