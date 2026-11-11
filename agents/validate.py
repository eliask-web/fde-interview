"""Step 2 (issue #4): check the fetched data is complete and sane."""

from agents.state import StepResult


def validate(ticker: str) -> StepResult:
    return {"ok": True, "detail": "validate stub"}
