"""Path helpers. The single gate for tickers and run folders.

Corpus (read only): data/filings/<TICKER>_<FORM>_<FILED>.txt plus manifest.json.
Run output: out/<TICKER>/ (gitignored). Issue #5 writes section files to
sections_dir(t)/<name>.md for each name in REQUIRED_SECTIONS.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_ROOT = REPO_ROOT / "out"
DATA_ROOT = REPO_ROOT / "data"
REQUIRED_SECTIONS = ("business", "risk_factors", "mdna")


def normalize_ticker(t: str) -> str:
    t = (t or "").strip().upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{0,9}", t):
        raise ValueError("invalid ticker")
    return t


def out_dir(ticker: str) -> Path:
    p = OUT_ROOT / normalize_ticker(ticker)
    p.mkdir(parents=True, exist_ok=True)
    return p


def sections_dir(ticker: str) -> Path:
    p = OUT_ROOT / normalize_ticker(ticker) / "sections"
    p.mkdir(parents=True, exist_ok=True)
    return p


def filings_dir() -> Path:
    return DATA_ROOT / "filings"


def manifest_path() -> Path:
    return filings_dir() / "manifest.json"
