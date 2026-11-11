"""Streamlit app: Dashboard and Before/After tabs."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, ROOT.as_posix())

import streamlit as st  # noqa: E402

from agents import graph, paths  # noqa: E402
from app import ui  # noqa: E402

st.set_page_config(page_title="Company briefing", layout="wide")
dash, before_after = st.tabs(["Dashboard", "Before/After"])

st.session_state.setdefault("runs", {})
st.session_state.setdefault("chats", {})
if "ticker_input" not in st.session_state:
    st.session_state["ticker_input"] = st.query_params.get("ticker", "AAPL")

with dash:
    st.text_input("Ticker", key="ticker_input")
    clicked = st.button("Brief me")
    try:
        t = paths.normalize_ticker(st.session_state["ticker_input"])
    except ValueError:
        t = None
        st.error("Please enter a valid ticker, like AAPL.")
    if t and clicked:
        st.query_params["ticker"] = t
        with st.spinner("Building the briefing..."):
            st.session_state["runs"][t] = graph.run_pipeline(t)
    if t:
        run = st.session_state["runs"].get(t)
        if run:
            st.write(f"Status: {run['status']}")
            cols = st.columns(4)
            for col, name in zip(cols, ui._STEPS):
                step = run["steps"].get(name)
                col.metric(name.capitalize(), ui.step_status(step))
                if step:
                    col.caption(step.get("detail", ""))
        folder = paths.OUT_ROOT / t
        quote = ui.read_quote(folder / "quote.csv")
        if quote:
            items = list(quote.items())
            st.metric(str(items[0][0]), str(items[0][1]))
            st.caption(", ".join(f"{k}: {v}" for k, v in items[1:]))
        brief = folder / "briefing.md"
        if brief.exists():
            st.markdown(brief.read_text(encoding="utf-8"))
        st.subheader("Ask a follow-up")
        hist = st.session_state["chats"].setdefault(t, [])
        for m in hist:
            with st.chat_message(m["role"]):
                st.write(m["content"])
                if m.get("sources"):
                    st.caption("Sources: " + "; ".join(ui.source_label(t, s) for s in m["sources"]))
        q = st.chat_input("Ask about this company")
        if q:
            r = graph.answer(q, t, [{"role": m["role"], "content": m["content"]} for m in hist])
            hist.append({"role": "user", "content": q})
            hist.append({"role": "assistant", "content": r["answer"], "sources": r["sources"]})
            st.rerun()

with before_after:
    doc = ROOT / "docs" / "BEFORE_AFTER.md"
    if doc.exists():
        st.markdown(doc.read_text())
    else:
        st.info("The before-and-after page is coming soon.")
