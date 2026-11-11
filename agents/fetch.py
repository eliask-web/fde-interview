"""Step 1 (issue #4): pull price data and filings for the ticker into out/<TICKER>/."""

from agents.state import StepResult


def fetch(ticker: str) -> StepResult:
    return {"ok": True, "detail": "fetch stub"}
