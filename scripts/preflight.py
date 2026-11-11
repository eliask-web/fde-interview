"""Preflight check: run before the session starts.

Confirms that packages import, keys are set, and each API answers.
It does not build any part of the prototype.

Usage: python scripts/preflight.py
"""

import importlib
import os
import sys

PACKAGES = [
    "langgraph", "langchain", "langchain_anthropic", "langchain_openai",
    "langchain_chroma", "chromadb", "langsmith", "streamlit",
    "deepeval", "pandas", "dotenv",
]
KEYS = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LANGSMITH_API_KEY"]


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

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
            reply = ChatAnthropic(model=model, max_tokens=10).invoke("Reply with OK.")
            results.append(check(f"Claude answers ({model})", bool(reply.content)))
        except Exception as e:
            results.append(check("Claude answers", False, str(e)[:120]))

    if os.getenv("OPENAI_API_KEY"):
        try:
            from langchain_openai import OpenAIEmbeddings
            vec = OpenAIEmbeddings(model="text-embedding-3-small").embed_query("test")
            results.append(check("OpenAI embeddings answer", len(vec) > 0, f"{len(vec)} dimensions"))
        except Exception as e:
            results.append(check("OpenAI embeddings answer", False, str(e)[:120]))

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
