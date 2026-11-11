"""Recent SEC filings tool backed by the EDGAR submissions API."""

import os
from functools import lru_cache

import requests
from dotenv import load_dotenv

from tools.retry import FetchError, retrying

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
BLOCK_MARKERS = ("<html", "request rate threshold exceeded", "access denied")
MAX_FILINGS = 5


def _user_agent() -> str:
    load_dotenv()
    ua = (os.getenv("SEC_USER_AGENT") or "").strip()
    if not ua:
        raise RuntimeError("SEC_USER_AGENT is not set")
    return ua


@retrying
def _get_json(url: str, user_agent: str):
    resp = requests.get(
        url,
        headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        timeout=10,
    )
    if resp.status_code != 200:
        raise FetchError(f"HTTP {resp.status_code} from {url}")
    body = resp.text.lower()
    if any(m in body for m in BLOCK_MARKERS):
        raise FetchError(f"block page from {url}")
    try:
        return resp.json()
    except ValueError as exc:
        raise FetchError(f"non-JSON body from {url}") from exc


@lru_cache(maxsize=64)
def _ticker_to_cik(ticker: str, user_agent: str) -> int:
    data = _get_json(TICKERS_URL, user_agent)
    for row in data.values():
        if str(row.get("ticker", "")).upper() == ticker.upper():
            return int(row["cik_str"])
    raise ValueError(f"unknown ticker {ticker}")


def get_recent_filings(ticker: str, form: str) -> list[dict]:
    """Get the most recent SEC filings of one form type for a ticker.

    Args:
        ticker: Stock ticker symbol, for example AAPL.
        form: SEC form type, either 10-K or 10-Q.

    Returns:
        Up to 5 dicts (newest first) with form, filing_date, accession and url.
    """
    ua = _user_agent()
    cik = _ticker_to_cik(ticker.strip().upper(), ua)
    data = _get_json(SUBMISSIONS_URL.format(cik=cik), ua)
    recent = data["filings"]["recent"]
    out = []
    for f, d, acc, doc in zip(
        recent["form"], recent["filingDate"], recent["accessionNumber"], recent["primaryDocument"]
    ):
        if f != form:
            continue
        url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}/{doc}"
        out.append({"form": f, "filing_date": d, "accession": acc, "url": url})
        if len(out) == MAX_FILINGS:
            break
    return out
