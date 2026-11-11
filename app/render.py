"""Step 4: turn out/<TICKER>/briefing.md into briefing.json. No streamlit here."""

import json
import re

from agents import paths
from agents.state import StepResult

_HEADING = re.compile(r"^#{1,3}\s+(.+?)\s*$")
_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+?)\s*$")


def parse_briefing(md: str, ticker: str) -> dict:
    sections: dict[str, list[str]] = {}
    sources: list[str] = []
    current = None
    for line in md.splitlines():
        m = _HEADING.match(line)
        if m:
            current = m.group(1)
            sections.setdefault(current, [])
            continue
        if current is None:
            continue
        sections[current].append(line)
        item = _ITEM.match(line)
        if item and current.strip().lower() == "sources":
            if "investment advice" not in item.group(1).lower():
                sources.append(item.group(1))
    return {
        "ticker": ticker,
        "sections": {k: "\n".join(v).strip() for k, v in sections.items()},
        "sources": sources,
    }


def render(ticker: str) -> StepResult:
    try:
        t = paths.normalize_ticker(ticker)
        folder = paths.OUT_ROOT / t
        data = parse_briefing((folder / "briefing.md").read_text(encoding="utf-8"), t)
        if not data["sections"]:
            return {"ok": False, "detail": "briefing has no headings", "paths": []}
        out = folder / "briefing.json"
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"ok": True, "detail": f"{len(data['sections'])} sections", "paths": [out.as_posix()]}
    except Exception as e:
        return {"ok": False, "detail": f"render failed: {type(e).__name__}", "paths": []}
