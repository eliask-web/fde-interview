"""Step 4 (issue #6): render the final briefing into out/<TICKER>/. No streamlit here."""

from agents.state import StepResult


def render(ticker: str) -> StepResult:
    return {"ok": True, "detail": "render stub"}
