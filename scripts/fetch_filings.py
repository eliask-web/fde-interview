"""Download the latest 10-K and 10-Q for each covered ticker from SEC EDGAR.

Writes plain-text filings to data/filings/ plus a manifest.json describing them.
The SEC requires a descriptive User-Agent, read from SEC_USER_AGENT in .env
(for example "Your Name your.email@example.com"). The value is never printed.

Usage:
    python scripts/fetch_filings.py            # all covered tickers
    python scripts/fetch_filings.py AAPL JPM   # a subset
    python scripts/fetch_filings.py --clean-only  # re-clean saved files, no download
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from dotenv import load_dotenv

# Covered tickers and their SEC CIK numbers. Anything else fails validation.
TICKERS: dict[str, int] = {
    "AAPL": 320193,
    "NVDA": 1045810,
    "JPM": 19617,
    "MSFT": 789019,
}
FORMS = ("10-K", "10-Q")
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "filings"
REQUEST_PAUSE_SECONDS = 0.2  # The SEC allows at most 10 requests per second.


class FetchError(RuntimeError):
    """Raised when the SEC cannot be reached or refuses the request."""


def validate_tickers(requested: list[str]) -> list[str]:
    """Return the requested tickers upper-cased, or raise ValueError for any not covered."""
    tickers = [t.upper() for t in requested] or list(TICKERS)
    unknown = [t for t in tickers if t not in TICKERS]
    if unknown:
        raise ValueError(
            f"Not covered: {', '.join(unknown)}. Covered tickers: {', '.join(TICKERS)}."
        )
    return tickers


def get(url: str, user_agent: str) -> bytes:
    """GET a URL from the SEC with the required User-Agent header."""
    request = urllib.request.Request(
        url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise FetchError(f"SEC returned HTTP {exc.code} for {url}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"Could not reach the SEC: {exc.reason}") from exc
    time.sleep(REQUEST_PAUSE_SECONDS)
    return body


class _TextExtractor(HTMLParser):
    """Collects visible text, skipping scripts, styles and inline XBRL headers."""

    SKIP = {"script", "style", "ix:header", "head"}
    BLOCK = {"p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.SKIP:
            self.skip_depth += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")
        elif tag in {"td", "th"}:
            self.parts.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    """Convert a filing's HTML to readable plain text."""
    parser = _TextExtractor()
    parser.feed(html)
    text = "".join(parser.parts).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return clean_text(text)


def clean_text(text: str) -> str:
    """Drop empty table rows and collapse runs of empty table cells."""
    text = re.sub(r"\|(?: *\|)+", "|", text)
    lines = [line for line in text.split("\n") if line.strip(" |")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def reclean_saved() -> int:
    """Re-apply clean_text to filings already in data/filings/ without downloading."""
    for path in sorted(OUT_DIR.glob("*.txt")):
        header, _, body = path.read_text(encoding="utf-8").partition("\n\n")
        path.write_text(header + "\n\n" + clean_text(body), encoding="utf-8")
        print(f"Cleaned {path.name}")
    return 0


def latest_filings(cik: int, user_agent: str) -> list[dict]:
    """Return the most recent filing of each form in FORMS for a company."""
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    data = json.loads(get(url, user_agent))
    recent = data["filings"]["recent"]
    found: dict[str, dict] = {}
    for i, form in enumerate(recent["form"]):
        if form in FORMS and form not in found:
            accession = recent["accessionNumber"][i]
            found[form] = {
                "company": data.get("name", ""),
                "form": form,
                "filing_date": recent["filingDate"][i],
                "period": recent["reportDate"][i],
                "url": (
                    f"https://www.sec.gov/Archives/edgar/data/{cik}/"
                    f"{accession.replace('-', '')}/{recent['primaryDocument'][i]}"
                ),
            }
        if len(found) == len(FORMS):
            break
    return [found[f] for f in FORMS if f in found]


def main(argv: list[str]) -> int:
    if argv == ["--clean-only"]:
        return reclean_saved()
    load_dotenv()
    user_agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not user_agent:
        print("SEC_USER_AGENT is empty. Set it in .env, e.g. 'Your Name you@example.com'.")
        return 2
    try:
        tickers = validate_tickers(argv)
    except ValueError as exc:
        print(exc)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for ticker in tickers:
        try:
            filings = latest_filings(TICKERS[ticker], user_agent)
            for filing in filings:
                text = html_to_text(get(filing["url"], user_agent).decode("utf-8", "replace"))
                name = f"{ticker}_{filing['form']}_{filing['filing_date']}.txt"
                title = f"{filing['company']} {filing['form']} for period ending {filing['period']}"
                header = (
                    f"Title: {title}\nTicker: {ticker}\nForm: {filing['form']}\n"
                    f"Filed: {filing['filing_date']}\nSource: {filing['url']}\n\n"
                )
                (OUT_DIR / name).write_text(header + text, encoding="utf-8")
                manifest.append({"file": name, "ticker": ticker, "title": title, **filing})
                print(f"Saved {name} ({len(text):,} characters)")
        except FetchError as exc:
            print(f"{ticker}: {exc}")
            return 1

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(manifest)} filings to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
