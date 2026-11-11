"""LangGraph pipeline: fetch -> validate -> summarize -> render.

Each node looks up its step function on the module at run time, so
later issues only replace function bodies.
"""

from langgraph.graph import END, START, StateGraph

import app.render as render_mod
from agents import fetch as fetch_mod
from agents import summarize as summarize_mod
from agents import validate as validate_mod
from agents.paths import normalize_ticker
from agents.state import PipelineState

_STEPS = [
    ("fetch", fetch_mod, "fetch"),
    ("validate", validate_mod, "validate"),
    ("summarize", summarize_mod, "summarize"),
    ("render", render_mod, "render"),
]


def _make_node(name, mod, attr):
    def node(state: PipelineState) -> dict:
        try:
            result = getattr(mod, attr)(state["ticker"])
        except Exception as e:
            result = {"ok": False, "detail": f"{name} raised {type(e).__name__}"}
        entry = {"ok": bool(result.get("ok")), "detail": result.get("detail", "")}
        if "status" in result:
            entry["status"] = result["status"]
        steps = {**state.get("steps", {}), name: entry}
        paths = list(state.get("paths", []))
        extra = result.get("paths")
        if isinstance(extra, list):
            paths.extend(p for p in extra if isinstance(p, str))
        if not entry["ok"]:
            status = entry.get("status") or "failed"
        elif name == "render":
            status = "ok"
        else:
            status = entry.get("status") or "running"
        return {"steps": steps, "paths": paths, "status": status}

    return node


def _route(state: PipelineState) -> str:
    return "next" if state.get("status") == "running" else "stop"


def _build():
    g = StateGraph(PipelineState)
    for name, mod, attr in _STEPS:
        g.add_node(name, _make_node(name, mod, attr))
    g.add_edge(START, "fetch")
    for i, (name, _, _) in enumerate(_STEPS):
        nxt = _STEPS[i + 1][0] if i + 1 < len(_STEPS) else END
        g.add_conditional_edges(name, _route, {"next": nxt, "stop": END})
    return g.compile()


_GRAPH = _build()


def run_pipeline(ticker: str) -> dict:
    try:
        t = normalize_ticker(ticker)
    except ValueError:
        return {"status": "failed", "steps": {}, "paths": []}
    final = _GRAPH.invoke(
        {"ticker": t, "status": "running", "steps": {}, "paths": []}
    )
    return {
        "status": final["status"],
        "steps": final["steps"],
        "paths": final["paths"],
    }


def answer(question: str, ticker: str, history: list) -> dict:
    """Stub, owned by issue #6."""
    return {"answer": "Chat is not built yet.", "sources": []}
