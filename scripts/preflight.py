"""Preflight check: run before the session starts.

Confirms that packages import, keys are set, and each API answers.
It does not build any part of the prototype.

Usage: python scripts/preflight.py
"""

import importlib
import os
import sys

PACKAGES = [
    "langgraph", "langchain", "langchain_anthropic", "langsmith", "streamlit",
    "pandas", "dotenv", "yfinance", "tenacity", "requests",
]
KEYS = ["PORTKEY_API_KEY", "PORTKEY_VIRTUAL_KEY", "SEC_USER_AGENT", "LANGSMITH_API_KEY"]


def check(label, ok, detail=""):
    print(f"[{'OK' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    return ok


def main():
    results = []
    v = sys.version_info
    results.append(check("Python 3.11 or newer", v >= (3, 11), f"{v.major}.{v.minor}"))

    for name in PACKAGES:
        try:
            importlib.import_module(name)
            results.append(check(f"import {name}", True))
        except Exception as e:
            results.append(check(f"import {name}", False, str(e)[:80]))

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    for key in KEYS:
        results.append(check(f"{key} is set", bool(os.getenv(key))))

    if os.getenv("PORTKEY_API_KEY") and os.getenv("PORTKEY_VIRTUAL_KEY"):
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from agents.llm import get_llm
            reply = get_llm().invoke("Reply with OK.")
            results.append(check("Claude answers (via Portkey)", bool(reply.content)))
        except Exception as e:
            results.append(check("Claude answers", False, str(e)[:120]))

    if os.getenv("LANGSMITH_API_KEY"):
        try:
            from langsmith import Client
            list(Client().list_projects(limit=1))
            results.append(check("LangSmith answers", True))
        except Exception as e:
            results.append(check("LangSmith answers", False, str(e)[:120]))

    failed = results.count(False)
    print(f"\n{len(results) - failed} passed, {failed} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
