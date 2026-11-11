"""Small helpers for the Streamlit page."""

import csv
import re
from pathlib import Path

from agents import paths

_STEPS = ("fetch", "validate", "summarize", "render")


def step_status(step: dict | None) -> str:
    if not step:
        return "pending"
    if step.get("ok"):
        return "ok"
    return step.get("status") or "failed"


def source_label(ticker: str, name: str) -> str:
    base = Path(name).name
    try:
        f = paths.sections_dir(ticker) / base
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^[#*\s]*(source|title)\s*:\s*", "", line, flags=re.I)
            line = re.sub(r"\(?https?://\S+\)?", "", line)
            line = re.sub(r"[#*_`]", "", line).strip(" -:")
            return f"{base} - {line}" if line else base
    except Exception:
        pass
    return base


def read_quote(path) -> dict | None:
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return rows[0] if rows else None
    except Exception:
        return None
