import json
from pathlib import Path

import pytest

from agents import paths, sections

WORDS = " ".join(["word"] * 300)
TOC = "Item 1.\nBusiness\nItem 1A.\nRisk Factors\nItem 7.\nManagement’s Discussion\n"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUT_ROOT", tmp_path / "out")
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path / "data")
    (tmp_path / "data" / "filings").mkdir(parents=True)
    return tmp_path


def write_corpus(env, k_text, q_text="", k_date="2026-02-01"):
    d = env / "data" / "filings"
    (d / "k.txt").write_text(k_text)
    (d / "q.txt").write_text(q_text)
    m = [
        {"file": "k.txt", "ticker": "AAA", "title": "AAA 10-K", "form": "10-K", "filing_date": k_date, "url": "http://k"},
        {"file": "q.txt", "ticker": "AAA", "title": "AAA 10-Q", "form": "10-Q", "filing_date": "2026-06-01", "url": "http://q"},
        {"file": "old.txt", "ticker": "AAA", "title": "old", "form": "10-K", "filing_date": "2020-01-01", "url": "http://o"},
    ]
    (d / "manifest.json").write_text(json.dumps(m))


def test_body_chosen_over_toc_and_stops_at_next_item():
    text = f"{TOC}\nItem 1. Business\n{WORDS}\nItem 1B. Unresolved\nafter {WORDS}"
    body, _ = sections.cut_section(text, sections.START_RES["business"])
    assert body.startswith("word") and "after" not in body


def test_item_1_does_not_match_1a():
    assert sections.START_RES["business"].search("Item 1A. Business") is None


def test_both_apostrophes():
    for q in "’'":
        body, _ = sections.cut_section(f"Item 7. Management{q}s Discussion\n{WORDS}", sections.START_RES["mdna"])
        assert body


def test_10q_part2_item2_not_used():
    text = f"Item 2. Unregistered Sales of Equity\n{WORDS}"
    body, detail = sections.cut_section(text, sections.START_RES["mdna_10q"])
    assert body is None and detail == "heading not found"


def test_short_body_reported_and_not_written(env):
    write_corpus(env, "Item 7. Management’s Discussion\nshort pointer\nItem 7A. x\n")
    r = sections.extract_sections("AAA")
    assert not r["mdna"]["ok"] and "under 200" in r["mdna"]["detail"]
    assert not (paths.sections_dir("AAA") / "mdna.md").exists()


def test_extract_writes_with_source_and_latest_filing(env):
    write_corpus(env, f"{TOC}Item 1. Business\n{WORDS}\nItem 1A. Risk Factors\n{WORDS}\nItem 7. Management’s Discussion\n{WORDS}\n")
    r = sections.extract_sections("AAA")
    assert r["business"]["ok"] and r["mdna"]["ok"] and not r["mdna_10q"]["ok"]
    assert (paths.sections_dir("AAA") / "business.md").read_text().startswith("Source: AAA 10-K (http://k)\n\n")


def test_stale_files_removed(env):
    write_corpus(env, "nothing")
    (paths.sections_dir("AAA") / "stale.md").write_text("x")
    sections.extract_sections("AAA")
    assert not (paths.sections_dir("AAA") / "stale.md").exists()


def test_missing_manifest_does_not_raise(env):
    r = sections.extract_sections("AAA")
    assert all(not v["ok"] for v in r.values())


def test_latest_filing():
    m = [{"ticker": "A", "form": "10-K", "filing_date": "2020-01-01"}, {"ticker": "A", "form": "10-K", "filing_date": "2021-01-01"}]
    assert sections.latest_filing(m, "A", "10-K")["filing_date"] == "2021-01-01"
    assert sections.latest_filing(m, "A", "10-Q") is None


def test_real_aapl_10k():
    real = Path(__file__).resolve().parent.parent / "data" / "filings" / "AAPL_10-K_2026-11-03.txt"
    if not real.exists():
        pytest.skip("corpus missing")
    text = real.read_text(encoding="utf-8", errors="replace")
    for n in ("business", "risk_factors", "mdna"):
        body, _ = sections.cut_section(text, sections.START_RES[n])
        assert body and len(body.split()) > 500
