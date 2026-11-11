import pytest

import agents.graph as graph
import agents.llm as llm
import agents.paths as paths
import app.render


@pytest.fixture(autouse=True)
def _roots(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUT_ROOT", tmp_path / "out")
    monkeypatch.setattr(paths, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(app.render, "render", lambda t: {"ok": True, "detail": "render stub"})


def test_happy_path():
    r = graph.run_pipeline("aapl")
    assert set(r) == {"status", "steps", "paths"}
    assert r["status"] == "ok"
    assert list(r["steps"]) == ["fetch", "validate", "summarize", "render"]
    assert isinstance(r["paths"], list)


def test_failing_node_stops(monkeypatch):
    monkeypatch.setattr(graph.validate_mod, "validate", lambda t: {"ok": False, "detail": "bad"})
    r = graph.run_pipeline("AAPL")
    assert r["status"] == "failed"
    assert list(r["steps"]) == ["fetch", "validate"]


def test_needs_human(monkeypatch):
    monkeypatch.setattr(
        graph.fetch_mod, "fetch",
        lambda t: {"ok": False, "detail": "x", "status": "needs_human"},
    )
    r = graph.run_pipeline("AAPL")
    assert r["steps"]["fetch"]["status"] == "needs_human"
    assert r["status"] == "needs_human"
    assert list(r["steps"]) == ["fetch"]


def test_exception_is_failure(monkeypatch):
    def boom(t):
        raise RuntimeError("secret detail")

    monkeypatch.setattr(graph.summarize_mod, "summarize", boom)
    r = graph.run_pipeline("AAPL")
    assert r["status"] == "failed"
    assert r["steps"]["summarize"]["detail"] == "summarize raised RuntimeError"
    assert "render" not in r["steps"]


def test_paths_merged_and_non_list_ignored(monkeypatch):
    monkeypatch.setattr(graph.fetch_mod, "fetch", lambda t: {"ok": True, "detail": "", "paths": ["a", 3]})
    monkeypatch.setattr(graph.validate_mod, "validate", lambda t: {"ok": True, "detail": "", "paths": "nope"})
    r = graph.run_pipeline("AAPL")
    assert r["status"] == "ok"
    assert r["paths"] == ["a"]


def test_render_wired_through_module(monkeypatch):
    monkeypatch.setattr(app.render, "render", lambda t: {"ok": True, "detail": "patched"})
    r = graph.run_pipeline("AAPL")
    assert r["steps"]["render"]["detail"] == "patched"


def test_invalid_ticker_skips_graph():
    for bad in ["", "../x", "a/b"]:
        assert graph.run_pipeline(bad) == {"status": "failed", "steps": {}, "paths": []}
        with pytest.raises(ValueError):
            paths.normalize_ticker(bad)


def test_path_helpers(tmp_path):
    assert paths.normalize_ticker(" aapl ") == "AAPL"
    assert paths.out_dir("aapl") == tmp_path / "out" / "AAPL"
    assert paths.out_dir("aapl").is_dir()
    s = paths.sections_dir("aapl")
    assert s == tmp_path / "out" / "AAPL" / "sections" and s.is_dir()
    assert paths.filings_dir() == tmp_path / "data" / "filings"
    assert not paths.filings_dir().exists()
    assert paths.manifest_path() == paths.filings_dir() / "manifest.json"
    assert paths.REQUIRED_SECTIONS == ("business", "risk_factors", "mdna")
    assert not hasattr(paths, "data_dir")


def test_answer_contract():
    r = graph.answer("q", "AAPL", [])
    assert set(r) == {"answer", "sources"}
    assert isinstance(r["answer"], str) and r["sources"] == []


def test_get_llm_portkey(monkeypatch):
    monkeypatch.setattr(llm, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setenv("PORTKEY_API_KEY", "pk")
    monkeypatch.setenv("PORTKEY_VIRTUAL_KEY", "vk")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-local-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "main-m")
    monkeypatch.setenv("ANTHROPIC_FAST_MODEL", "fast-m")
    m = llm.get_llm()
    assert m.model == "main-m"
    assert "portkey.ai" in m.anthropic_api_url
    assert m.default_headers["x-portkey-api-key"] == "pk"
    assert m.default_headers["x-portkey-virtual-key"] == "vk"
    assert m.anthropic_api_key.get_secret_value() == "portkey-routed"
    assert llm.get_llm(fast=True).model == "fast-m"


def test_streamlit_app_runs():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(paths.REPO_ROOT / "app" / "main.py"), default_timeout=30).run()
    assert not at.exception
    assert [t.label for t in at.tabs] == ["Dashboard", "Before/After"]
