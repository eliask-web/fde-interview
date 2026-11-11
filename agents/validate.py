"""Step 2 (issue #5): extract sections and check the data is complete and sane."""

import csv
import json
import math
import re
from datetime import date, datetime

from agents import paths
from agents.sections import extract_sections, latest_filing, load_manifest
from agents.state import StepResult

MIN_SECTION_WORDS = 500
ERROR_PAGE_RE = re.compile(
    r"(access denied|page not found|error\s+404|404\s+(error|not found)|"
    r"not found\s*\(404\)|request blocked|enable javascript and cookies)",
    re.I,
)


def _check(name, ok, detail=""):
    return {"name": name, "ok": bool(ok), "detail": detail}


def _safe(name, fn):
    try:
        return _check(name, *fn())
    except Exception as e:
        return _check(name, False, f"check error ({type(e).__name__})")


def _read_csv(ticker, name):
    with (paths.out_dir(ticker) / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _corpus(ticker):
    m = load_manifest()
    t = paths.normalize_ticker(ticker)
    missing = [f for f in ("10-K", "10-Q") if latest_filing(m, t, f) is None]
    return (not missing, f"missing in corpus: {', '.join(missing)}" if missing else "10-K and 10-Q found")


def _recent(ticker, form, max_days, today):
    rows = [r for r in _read_csv(ticker, "filings.csv") if r.get("form") == form]
    if not rows:
        return False, f"no {form} in filings.csv"
    d = max(date.fromisoformat(r["filing_date"]) for r in rows)
    age = (today - d).days
    return age <= max_days, f"latest {form} filed {d} ({age} days old, limit {max_days})"


def _sections(ticker, extraction):
    ex = extraction if extraction is not None else extract_sections(ticker)
    bad = []
    for name in paths.REQUIRED_SECTIONS:
        info = ex.get(name) or {}
        words = 0
        if info.get("ok") and info.get("path"):
            body = open(info["path"], encoding="utf-8").read().split("\n", 2)
            words = len((body[2] if len(body) > 2 else "").split())
        if words < MIN_SECTION_WORDS:
            bad.append(f"{name}: {info.get('detail') or 'missing'} ({words} words)")
    return (not bad, "; ".join(bad) if bad else "all required sections present")


def _error_pages(ticker):
    sdir = paths.sections_dir(ticker)
    hits = [p.name for p in sdir.glob("*.md") if ERROR_PAGE_RE.search(p.read_text(encoding="utf-8"))]
    return (not hits, f"error-page text in {', '.join(hits)}" if hits else "none found")


def _quote(ticker, today):
    rows = _read_csv(ticker, "quote.csv")
    if not rows:
        return False, "quote.csv is empty"
    q = rows[0]
    for k in ("price", "change", "change_pct"):
        if not math.isfinite(float(q[k])):
            return False, f"{k} is not finite"
    age = (today - date.fromisoformat(q["as_of"])).days
    if age < -1 or age > 5:
        return False, f"as_of {q['as_of']} is {age} days old"
    return True, f"as_of {q['as_of']}"


def run_checks(ticker: str, extraction: dict | None = None, today: date | None = None) -> dict:
    today = today or date.today()
    checks = [
        _safe("corpus_has_filings", lambda: _corpus(ticker)),
        _safe("filing_10q_recent", lambda: _recent(ticker, "10-Q", 135, today)),
        _safe("filing_10k_recent", lambda: _recent(ticker, "10-K", 400, today)),
        _safe("sections_present", lambda: _sections(ticker, extraction)),
        _safe("no_error_pages", lambda: _error_pages(ticker)),
        _safe("quote_valid", lambda: _quote(ticker, today)),
    ]
    return {
        "ticker": str(ticker),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "checks": checks,
        "passed": all(c["ok"] for c in checks),
    }


def validate(ticker: str) -> StepResult:
    try:
        extraction = extract_sections(ticker)
        report = run_checks(ticker, extraction)
        p = paths.out_dir(ticker) / "validation.json"
        p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception as e:
        return {"ok": False, "detail": f"validate failed ({type(e).__name__})", "paths": []}
    failed = [c["name"] for c in report["checks"] if not c["ok"]]
    detail = "all checks passed" if report["passed"] else "failed: " + ", ".join(failed)
    return {"ok": report["passed"], "detail": detail, "paths": [str(p)]}
