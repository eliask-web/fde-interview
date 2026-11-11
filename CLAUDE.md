# CLAUDE.md

> Product context for this build: see `docs/PROJECT-BRIEF.md` (written at kickoff from the scenario). What "done" means for the whole prototype: see `docs/RUBRIC_CHECKLIST.md`.

This repo runs on the trail-blazer-flow harness (github.com/msummer/trail-blazer-flow, MIT, by Mark Summer). Work moves through GitHub issues: the planner writes a plan, the plan is approved, the implementer builds it, the verifier reviews it, and a PR opens for a human to merge. Every line of application code is written by Claude.

## Conventions & architecture

The prototype is an AI assistant built in one sitting. The stack is decided. Do not re-debate it in plans.

- **Language:** Python 3.11 or 3.12.
- **Agent framework:** LangGraph. One graph with a router node and specialist agent nodes (at least a retriever agent, an action agent that makes tool calls, and a reviewer agent that checks answers before they go out). Short-term memory through the LangGraph checkpointer.
- **LLM:** Claude through `langchain-anthropic`. Main model from `ANTHROPIC_MODEL`, cheaper model for the reviewer and the eval judge from `ANTHROPIC_FAST_MODEL`.
- **Embeddings:** OpenAI `text-embedding-3-small` through `langchain-openai`.
- **Vector store:** Chroma, persisted to `./chroma_db`. The app rebuilds the index at startup when that folder is missing, because Railway's disk can reset.
- **Tool calling:** Real model tool calls through `bind_tools`. The model decides when to call a tool and with which inputs. The app never calls a tool directly to fake a tool call.
- **Front end:** Streamlit. Tab 1 is the chat, with sources listed under each answer. Tab 2 is a plain-language before-and-after page for a non-technical reader, with no technical words.
- **Tracing:** LangSmith, turned on through environment variables only.
- **Evaluation:** DeepEval with Claude as the judge (`deepeval.models.AnthropicModel`): faithfulness, answer relevancy and contextual relevancy over a golden set of 8 to 10 questions in `eval/golden_set.jsonl`, printed as a table. Do not use RAGAS: its current release fails to import with the current LangChain.
- **Deployment:** Local first, then Railway. Start command: `streamlit run app/main.py --server.port $PORT --server.address 0.0.0.0`.

### Repository layout

| Path | What lives there |
|---|---|
| `agents/` | LangGraph graph, router, agent nodes, guardrails, memory. Entry point `agents/graph.py` exposes `answer(question: str, thread_id: str) -> dict` returning `{"answer", "sources", "confidence"}` |
| `app/` | Streamlit app, `app/main.py` |
| `data/` | Input data for the scenario. Read only |
| `docs/` | Project brief, rubric checklist, kickoff prompts |
| `eval/` | Golden set and `eval/run_eval.py` |
| `rag/` | Loading, chunking, embedding, Chroma, retriever. Entry point `rag/retriever.py` exposes `retrieve(query: str, k: int = 5) -> list[dict]`, each with `text`, `source` and `score` |
| `scripts/` | Preflight and helper scripts |
| `tests/` | pytest tests |
| `tools/` | Functions the model can call, each with a docstring and typed arguments |

The entry points above are the contract between modules. A plan that changes one must say so.

### Rules

- Secrets only in `.env`, read with `python-dotenv`. Never commit `.env`, never read or print it, never print a key. The session is screen-recorded.
- Every answer cites its sources by title or file name.
- When retrieval finds nothing relevant, the system says so and does not guess.
- Guardrails: refuse off-topic requests, ignore instructions that arrive inside retrieved documents or user text that tries to override the system prompt, and return low-confidence answers with a note to check with a person.
- Unit tests never call a paid API. Mock the LLM and the embeddings. A live test, if any, is marked `@pytest.mark.live` and skipped by default.
- Prefer simple and working over clever. Keep modules small.
- American English in all text and labels.

## Setup

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in the keys
```

## Verification

Run from the repo root with the virtual environment active. A change is done when all three pass.

```bash
pip install -q -r requirements.txt
python -m compileall -q agents app rag tools eval scripts
pytest -q -m "not live"
```

## Plan auto-approval policy

Auto-approve plans that are size S or M and only touch `agents/`, `app/`, `eval/`, `rag/`, `tools/`, `tests/`, `scripts/`, `data/` or `requirements.txt`. Plans that touch `CLAUDE.md`, `.claude/`, `docs/RUBRIC_CHECKLIST.md`, deployment configuration, or how secrets are read require manual approval.

## Workflow

- Issue #1 is always the walking skeleton: every module above with its entry point stubbed to the contract, a Streamlit page that runs, and tests that pass. Record the baseline after it merges.
- After the skeleton, independent issues run in worktree-parallel mode (up to 4 at once): retrieval, agents and tools, front end, then guardrails and memory, and the evaluation runner.
- A second Claude Code session (the side window) works in its own worktree on `side-*` branches and opens its own PRs. It owns `eval/golden_set.jsonl`, `docs/BEFORE_AFTER.md`, `docs/DEMO.md`, `docs/DEPLOY.md` and `railway.json`, and never edits `agents/`, `app/`, `rag/`, `tools/` or `tests/`. Plans must not touch the files it owns.
- PRs are merged by the human. The harness never merges.
- Deploys happen by hand from `main` on Railway, following `docs/DEPLOY.md`.

## Non-goals

No user accounts, no admin pages, no CI pipeline, no data editing in the app, no production hardening beyond the guardrails above.
