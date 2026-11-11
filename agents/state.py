"""Shared types for the briefing pipeline.

Status values: running, ok, failed, needs_human.
"""

from typing import TypedDict


class StepResult(TypedDict, total=False):
    ok: bool
    detail: str
    status: str  # optional, e.g. "needs_human"
    paths: list[str]  # optional, files the step wrote


class PipelineState(TypedDict, total=False):
    ticker: str
    status: str
    steps: dict
    paths: list
