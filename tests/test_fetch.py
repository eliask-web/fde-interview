import csv
import json
from types import SimpleNamespace

import pandas as pd
import pytest
import tenacity
from langchain_core.messages import AIMessage

import agents.fetch as af
import tools.market as market
import tools.sec as sec
from tools.retry import FetchError

TICKERS = {"0": {"cik_str": 320193, "ticker": "AAPL"}}
SUBS = {"filings": {"recent": {
    "form": ["10-Q", "10-K", "8-K"],
    "filingDate": ["2025-08-01", "2024-11-01", "2025-09-01"],
    "accessionNumber": ["0000320193-25-000073", "0000320193-24-000123", "x"],
    "primaryDocument": ["q.htm", "k.htm", "e.htm"],
}}}


class Resp:
    def __init__(self, status=200, body=None, text=None):
        self.status_code = status
        self.text = text if text is not None else json.dumps(body)

    def json(self):
        return json.loads(self.text)


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("SEC_USER_AGENT", "Test test@example.com")
    monkeypatch.setattr(sec, "load_dotenv", lambda: None)
    sec._ticker_to_cik.cache_clear()
    for fn in (sec._get_json, market._history):
        monkeypatch.setattr(fn.retry, "wait", tenacity.wait_none())
    monkeypatch.setattr(af, "out_dir", lambda t: tmp_path)
    calls = {"get": [], "hist": 0, "tmp": tmp_path}

    def fake_get(url, headers=None, timeout=None):
        calls["get"].append((url, headers))
        if calls.get("mode") == "503":
            return Resp(503, {})
        if calls.get("mode") == "html":
            return Resp(200, text="<html>Request Rate Threshold Exceeded</html>")
        return Resp(200, TICKERS if "company_tickers" in url else SUBS)

    monkeypatch.setattr(sec.requests, "get", fake_get)

    class FakeTicker:
        fast_info = {"currency": "USD"}

        def __init__(self, t):
            pass

        def history(self, period):
            calls["hist"] += 1
            if calls.get("empty"):
                return pd.DataFrame()
            return pd.DataFrame({"Close": [100.0, 102.0]},
                                index=pd.to_datetime(["2025-01-02", "2025-01-03"]))

    monkeypatch.setattr(market, "yf", SimpleNamespace(Ticker=FakeTicker))
    yield calls
    sec._ticker_to_cik.cache_clear()


def script(monkeypatch, turns):
    rec = {"bound": None, "invokes": []}

    class LLM:
        def bind_tools(self, tools):
            rec["bound"] = tools
            return self

        def invoke(self, messages):
            rec["invokes"].append(list(messages))
            return turns[len(rec["invokes"]) - 1]

    monkeypatch.setattr(af, "get_llm", lambda: LLM())
    return rec


def tc(name, id, **args):
    return {"name": name, "args": args, "id": id}


def all_calls(t="AAPL"):
    return [tc("get_stock_quote", "1", ticker=t),
            tc("get_recent_filings", "2", ticker=t, form="10-Q"),
            tc("get_recent_filings", "3", ticker=t, form="10-K")]


def test_happy_path(env, monkeypatch):
    rec = script(monkeypatch, [AIMessage("", tool_calls=all_calls())])
    res = af.fetch("aapl")
    assert res["ok"] and "status" not in res
    assert isinstance(res["paths"], list) and len(res["paths"]) == 2
    assert len(rec["bound"]) == 2
    rows = list(csv.DictReader(open(env["tmp"] / "filings.csv")))
    assert rows[0]["url"] == "https://www.sec.gov/Archives/edgar/data/320193/000032019325000073/q.htm"
    assert [r["form"] for r in rows] == ["10-Q", "10-K"]
    q = list(csv.DictReader(open(env["tmp"] / "quote.csv")))[0]
    assert q["price"] == "102.0" and q["as_of"] == "2025-01-03"
    assert all(h["User-Agent"] == "Test test@example.com" for _, h in env["get"])


def test_503_needs_human(env, monkeypatch):
    env["mode"] = "503"
    script(monkeypatch, [AIMessage("", tool_calls=all_calls())])
    res = af.fetch("AAPL")
    assert res["status"] == "needs_human" and res["attempts"] == 3
    assert len(env["get"]) == 3


def test_html_block_page(env, monkeypatch):
    env["mode"] = "html"
    script(monkeypatch, [AIMessage("", tool_calls=all_calls())])
    assert af.fetch("AAPL")["status"] == "needs_human"
    assert len(env["get"]) == 3


def test_non_json_raises_after_3(monkeypatch):
    monkeypatch.setattr(sec._get_json.retry, "wait", tenacity.wait_none())
    n = []
    monkeypatch.setattr(sec.requests, "get", lambda *a, **k: n.append(1) or Resp(200, text="nope"))
    with pytest.raises(FetchError):
        sec._get_json("http://x", "ua")
    assert len(n) == 3


def test_missing_user_agent(env, monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT")
    script(monkeypatch, [AIMessage("", tool_calls=all_calls())])
    res = af.fetch("AAPL")
    assert res["status"] == "failed" and "SEC_USER_AGENT" in res["detail"]
    assert env["get"] == []


def test_recovers_on_second_turn(env, monkeypatch):
    first = AIMessage("", tool_calls=all_calls()[:2])
    second = AIMessage("", tool_calls=[tc("get_recent_filings", "9", ticker="AAPL", form="10-K")])
    rec = script(monkeypatch, [first, second])
    assert af.fetch("AAPL")["ok"]
    ids = [m.tool_call_id for m in rec["invokes"][1] if m.type == "tool"]
    assert ids == ["1", "2"]


def test_omitted_twice(env, monkeypatch):
    rec = script(monkeypatch, [AIMessage("", tool_calls=all_calls()[:2]), AIMessage("")])
    res = af.fetch("AAPL")
    assert res["status"] == "needs_human"
    assert len(rec["invokes"]) == 2


def test_empty_history(env, monkeypatch):
    env["empty"] = True
    script(monkeypatch, [AIMessage("", tool_calls=all_calls())])
    assert af.fetch("AAPL")["status"] == "needs_human"
    assert env["hist"] == 3


def test_wrong_ticker_not_executed(env, monkeypatch):
    calls = [tc("get_stock_quote", "1", ticker="MSFT")] + all_calls()[1:]
    script(monkeypatch, [AIMessage("", tool_calls=calls), AIMessage("")])
    res = af.fetch("AAPL")
    assert res["status"] == "needs_human"
    assert env["hist"] == 0
