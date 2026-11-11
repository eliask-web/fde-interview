"""Cut filing sections out of the local corpus in plain Python (issue #5)."""

import json
import re

from agents import paths

MIN_BODY_WORDS = 200
_Q = "[’']"
START_RES = {
    "business": re.compile(r"^\s*Item\s+1\.?\s+Business\b", re.I | re.M),
    "risk_factors": re.compile(r"^\s*Item\s+1A\.?\s+Risk\s+Factors\b", re.I | re.M),
    "mdna": re.compile(rf"^\s*Item\s+7\.?\s+Management{_Q}s\s+Discussion", re.I | re.M),
    "mdna_10q": re.compile(rf"^\s*Item\s+2\.?\s+Management{_Q}s\s+Discussion", re.I | re.M),
}
END_RE = re.compile(r"^\s*Item\s+\d+[A-Z]?\b", re.I | re.M)
SECTION_FORM = {"business": "10-K", "risk_factors": "10-K", "mdna": "10-K", "mdna_10q": "10-Q"}


def load_manifest() -> list:
    return json.loads(paths.manifest_path().read_text(encoding="utf-8"))


def latest_filing(manifest: list, ticker: str, form: str) -> dict | None:
    rows = [r for r in manifest if r.get("ticker") == ticker and r.get("form") == form]
    return max(rows, key=lambda r: r.get("filing_date", "")) if rows else None


def cut_section(text: str, start_re, min_words: int = MIN_BODY_WORDS):
    found = False
    for m in start_re.finditer(text):
        found = True
        nl = text.find("\n", m.end())
        start = len(text) if nl == -1 else nl + 1
        end_m = END_RE.search(text, start)
        body = text[start : end_m.start() if end_m else len(text)].strip()
        if len(body.split()) > min_words:
            return body, "ok"
    return None, "heading found but body under 200 words" if found else "heading not found"


def extract_sections(ticker: str) -> dict:
    result = {n: {"ok": False, "detail": "", "path": None, "words": 0} for n in START_RES}
    try:
        sdir = paths.sections_dir(ticker)
        for old in sdir.glob("*.md"):
            old.unlink()
        manifest = load_manifest()
    except Exception as e:
        for r in result.values():
            r["detail"] = f"manifest unavailable ({type(e).__name__})"
        return result
    t = paths.normalize_ticker(ticker)
    cache = {}
    for name, rx in START_RES.items():
        try:
            form = SECTION_FORM[name]
            row = latest_filing(manifest, t, form)
            if row is None:
                result[name]["detail"] = f"no {form} in corpus"
                continue
            if form not in cache:
                cache[form] = (paths.filings_dir() / row["file"]).read_text(
                    encoding="utf-8", errors="replace"
                )
            body, detail = cut_section(cache[form], rx)
            result[name]["detail"] = detail
            if body is None:
                continue
            p = sdir / f"{name}.md"
            p.write_text(f"Source: {row['title']} ({row['url']})\n\n{body}\n", encoding="utf-8")
            result[name].update(ok=True, path=str(p), words=len(body.split()))
        except Exception as e:
            result[name]["detail"] = f"extraction error ({type(e).__name__})"
    return result
