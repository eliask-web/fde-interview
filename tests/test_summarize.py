import json

import pytest

from agents import paths, summarize


class FakeLLM:
    def __init__(self, exc=None):
        self.exc, self.msgs = exc, None

    def invoke(self, msgs):
        if self.exc:
            raise self.exc
        self.msgs = msgs

        class R:
            content = [{"type": "text", "text": "Snapshot body"}]

        return R()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "OUT_ROOT", tmp_path / "out")
    sd = paths.sections_dir("AAA")
    (sd / "business.md").write_text("Source: AAA 10-K (http://k)\n\nbiz text\n")
    (paths.out_dir("AAA") / "validation.json").write_text(json.dumps({"passed": True}))
    return tmp_path


def patch_llm(monkeypatch, llm):
    monkeypatch.setattr(summarize, "get_llm", lambda *a, **k: llm)


def test_briefing_has_text_sources_footer(env, monkeypatch):
    llm = FakeLLM()
    patch_llm(monkeypatch, llm)
    res = summarize.summarize("AAA")
    assert res["ok"]
    text = (paths.out_dir("AAA") / "briefing.md").read_text()
    assert "Snapshot body" in text and "## Sources" in text and "AAA 10-K (http://k)" in text
    assert text.rstrip().endswith("Not investment advice.")
    assert '<filing_section name="business" source="AAA 10-K (http://k)">' in llm.msgs[1][1]


def test_truncate():
    out = summarize.truncate_sections({"a": "x " * 100, "b": "y " * 100}, total_words=20)
    assert all(len(v.split()) == 10 for v in out.values())


@pytest.mark.parametrize("report", [{"passed": False}, None])
def test_skipped_when_not_validated(env, monkeypatch, report):
    calls = []
    monkeypatch.setattr(summarize, "get_llm", lambda *a, **k: calls.append(1) or FakeLLM())
    vj = paths.out_dir("AAA") / "validation.json"
    if report is None:
        vj.unlink()
    else:
        vj.write_text(json.dumps(report))
    assert not summarize.summarize("AAA")["ok"]
    assert calls == []
    assert not (paths.out_dir("AAA") / "briefing.md").exists()


def test_llm_exception_reports_class_only(env, monkeypatch):
    patch_llm(monkeypatch, FakeLLM(ValueError("secret-key-123")))
    res = summarize.summarize("AAA")
    assert not res["ok"] and "ValueError" in res["detail"] and "secret" not in res["detail"]
