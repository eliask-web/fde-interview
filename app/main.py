"""Streamlit app: Dashboard and Before/After tabs (placeholder)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, ROOT.as_posix())

import streamlit as st  # noqa: E402

from agents.graph import run_pipeline  # noqa: E402

st.set_page_config(page_title="Company briefing", layout="wide")
dash, before_after = st.tabs(["Dashboard", "Before/After"])

with dash:
    ticker = st.text_input("Ticker", value="AAPL")
    if st.button("Brief me"):
        result = run_pipeline(ticker)
        st.write(f"Status: {result['status']}")
        cols = st.columns(4)
        for col, name in zip(cols, ["fetch", "validate", "summarize", "render"]):
            step = result["steps"].get(name)
            col.metric(name, "skipped" if step is None else ("ok" if step["ok"] else "failed"))
            if step:
                col.caption(step["detail"])

with before_after:
    doc = ROOT / "docs" / "BEFORE_AFTER.md"
    if doc.exists():
        st.markdown(doc.read_text())
    else:
        st.info("The before-and-after page is coming soon.")
