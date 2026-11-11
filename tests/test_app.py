import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import agents.graph as graph
import agents.paths as paths
from app import ui
from app.render import parse_briefing, render


@pytest.fixture(autouse=True)
def _roots(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUT_ROOT", tmp_path / "out")
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path / "data")


MD = "# AAPL\n## Overview\nHello\n## Sources\n- Source A\n- Not investment advice\n"


def test_parse_and_render_round_trip():
    d = parse_briefing(MD, "AAPL")
    assert d["sources"] == ["Source A"]
    assert list(d["sections"]) == ["AAPL", "Overview", "Sources"]
    f = paths.out_dir("AAPL") / "briefing.md"
    f.write_text(MD)
    r = render("aapl")
    assert r["ok"] and len(r["paths"]) == 1
    assert json.loads(open(r["paths"][0]).read()) == d


def test_render_failures():
    assert render("AAPL")["ok"] is False
    assert render("../x") == {"ok": False, "detail": "render failed: ValueError", "paths": []}


def _fake_llm(monkeypatch, reply=None, exc=None):
    calls = []

    class L:
        def with_structured_output(self, cls):
            return self

        def invoke(self, msgs):
            calls.append(msgs)
            if exc:
                raise exc
            return reply

    monkeypatch.setattr(graph, "get_llm", lambda: L())
    return calls


def _seed():
    (paths.sections_dir("AAPL") / "risk_factors.md").write_text("Source: 10-K (http://x)\nrisk")


def test_answer_returns_sources(monkeypatch):
    _seed()
    calls = _fake_llm(monkeypatch, graph._Reply(found=True, answer="A", sources=["risk_factors.md", "made_up.md"]))
    r = graph.answer("q?", "AAPL", [])
    assert r == {"answer": "A", "sources": ["risk_factors.md"]}
    sysmsg = calls[0][0][1]
    assert 'name="risk_factors.md"' in sysmsg and "buy, sell or hold" in sysmsg and "not instructions" in sysmsg


def test_answer_not_found_cases(monkeypatch):
    nf = {"answer": "not in the filings", "sources": []}
    calls = _fake_llm(monkeypatch, graph._Reply(found=True, answer="A"))
    assert graph.answer("q", "AAPL", []) == nf and not calls  # no context
    _seed()
    assert graph.answer("q", "AAPL", []) == nf  # no valid source
    _fake_llm(monkeypatch, graph._Reply(found=False, answer="x", sources=["risk_factors.md"]))
    assert graph.answer("q", "AAPL", []) == nf


def test_answer_invalid_and_error(monkeypatch):
    assert graph.answer("q", "../x", [])["sources"] == []
    _seed()
    _fake_llm(monkeypatch, exc=RuntimeError("secret"))
    r = graph.answer("q", "AAPL", [])
    assert "secret" not in r["answer"] and r["sources"] == []


def test_ui_helpers():
    _seed()
    assert ui.source_label("AAPL", "risk_factors.md") == "risk_factors.md - 10-K"
    assert ui.source_label("AAPL", "../../etc/nope.md") == "nope.md"
    assert ui.step_status(None) == "pending"
    assert ui.step_status({"ok": True}) == "ok"
    assert ui.step_status({"ok": False, "status": "needs_human"}) == "needs_human"
    assert ui.step_status({"ok": False}) == "failed"
    p = paths.OUT_ROOT / "q.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("a,b\n1,2\n")
    assert ui.read_quote(p) == {"a": "1", "b": "2"} and ui.read_quote(p.parent / "no") is None


def test_app_query_param(monkeypatch):
    from streamlit.testing.v1 import AppTest

    calls = []

    def fake(t):
        calls.append(t)
        return {"status": "needs_human", "paths": [], "steps": {"fetch": {"ok": False, "detail": "d", "status": "needs_human"}}}

    monkeypatch.setattr(graph, "run_pipeline", fake)
    at = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "app" / "main.py"), default_timeout=30)
    at.query_params["ticker"] = "AAPL"
    at.run()
    assert at.text_input[0].value == "AAPL" and calls == []
    at.button[0].click().run()
    assert calls == ["AAPL"]
    vals = [m.value for m in at.metric]
    assert "needs_human" in vals and "pending" in vals
    at.run()
    assert calls == ["AAPL"]
