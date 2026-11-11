# AI history: Claude chat used as interview copilot

Date: 2026-11-11 (Eastern time), about 9:41 AM to 12:24 PM
Tool: Claude (claude.ai chat, Opus 5.5), alongside two Claude Code sessions (T1 main window, T2 side window)
Purpose: turn the interview scenario into kickoff prompts for the harness, handle mid-session changes, recover lost terminals, and build the pitch slide and a dashboard sketch.

User messages are verbatim. Claude replies are condensed, with the prompts it produced kept in full where they were pasted into Claude Code.

---

## 1. Setup

**User:** I'm in a live 2.5-hour AI prototyping interview. My repo is a copy of eliask-web/fde-harness-template. Read its CLAUDE.md, docs/RUBRIC_CHECKLIST.md and docs/KICKOFF_PROMPTS.md now. When I paste the scenario, give me these three, short: 1. The architecture in 8 lines I can say out loud. 2. The main-window kickoff prompt for Claude Code, with the scenario and the six issues adapted to it. 3. The side-window prompt adapted to it. If the scenario gives no data, the side window first generates 20 to 30 realistic documents into data/, then writes the golden set. Then stay ready for quick questions. No long explanations.

**Claude:** Cloned the template and read the three files plus `.claude/LESSONS.md`. Key points noted: issue 1 is the walking skeleton, the side window owns the golden set and demo/deploy docs, and git commands must stay out of subagent Bash calls.

## 2. Scenario

**User:** (attached AI_Solution_Prototype_Challenge.pdf) prototype exercise

**Claude:** Read the challenge (Manufacturing, Finance, Healthcare or Open Choice; Portkey gateway with Claude Sonnet 4.5; deliverables are a prototype, one slide and a 20-minute interview). Recommended Manufacturing and drafted the architecture, T1 prompt and T2 prompt for it, with the LLM routed through Portkey via `ChatOpenAI(base_url=PORTKEY_BASE_URL, ...)` and a direct Anthropic fallback.

## 3. Switch to Finance

**User:** nope Wealth management

**Claude:** Rebuilt for the Finance scenario: live quote as a tool call (yfinance), SEC EDGAR filings list as a second tool, recent 10-K, 10-Q and 8-K text as the knowledge base. Recommended real SEC filings over generated documents, pulled with edgartools for AAPL, MSFT, NVDA, JPM and JNJ. Guardrails added: no buy or sell advice, every number cited, "not investment advice" footer. Prepared panel lines: filings change quarterly while quotes change every second; scale with a nightly EDGAR sync; swap yfinance for the firm's market data feed.

## 4. Client clarification: four-stage pipeline

**User:** Let's add these additional clarifying steps from the convo text: (transcript of the conversation with the interviewer, describing: a first agent that connects to the API, retries, avoids being blocked as a bot, escalates to a human after repeated failures, and writes a CSV; a second agent that applies rules to check the latest date, text, errors and cleanliness, then summarizes against given criteria into an MD file; then Python code that turns the summary into JSON and HTML for a dashboard at a specific URL. The interviewer summarized it as retrieval, deterministic validation, summarization, and an application layer to render the result.)

**Claude:** Mapped it to a LangGraph pipeline: fetch, validate, summarize, review, render.

Prompt given to T1:

```
The client clarified the flow. Update the backlog to match. Do not redo merged work. Check each issue's state first: if an issue is not yet implemented, edit it; if it is implemented, create a new issue instead.

New flow per ticker, as a LangGraph pipeline: fetch -> validate -> summarize -> review -> render. The follow-up chat stays.

1. Fetch agent: bind_tools with get_stock_quote and get_recent_filings. Each tool retries with exponential backoff (tenacity, 3 attempts), stays under the SEC rate limit (10 requests per second), sends SEC_USER_AGENT, and recognizes a block or error page as a failure. After 3 failures the run stops with status "needs_human". Writes out/<TICKER>/quote.csv and out/<TICKER>/filings.csv.
2. Validation: agents/validate.py, plain Python, no LLM. Rules: latest 10-Q within 135 days, latest 10-K within 400 days, required sections present with at least 500 words each, no error-page text, numeric and fresh quote fields, no empty or duplicate rows. Writes validation.json. A fail stops the pipeline and shows which rule failed.
3. Summarizer: runs only after validation passes. Writes briefing.md against fixed criteria (Snapshot, What the company does, Latest results with 3 numbers, Top 3 risks, What changed, Sources). The reviewer agent checks it.
4. Render: app/render.py, plain Python, no LLM. briefing.json, then a Streamlit Dashboard tab linkable at ?ticker=<TICKER>, with a status strip (Fetch, Validate, Summarize, Review).

Add out/ to .gitignore. Unit tests mock the network and the LLM, including a fetch that fails 3 times and a validation fail on a stale filing.
```

Prompt given to T2: add a TSLA validation-fail scenario and an empty SEC_USER_AGENT fetch-failure scenario to docs/DEMO.md, and rewrite docs/BEFORE_AFTER.md as gather, check, summarize, show.

Panel line: the LLM only does the two jobs that need judgment, choosing what to fetch and summarizing. Validation and rendering are plain code, so they are repeatable and auditable.

## 5. Simplify to an MVP

**User:** Also, simplify tech stack for a quick MVP so we are not wasting time but have enough for a demo

**Claude:** Cut Chroma, OpenAI embeddings, the checkpointer, DeepEval, Railway, the static HTML file and the reviewer agent (stretch). Kept LangGraph with 4 nodes, Portkey, yfinance, the EDGAR submissions API, files in out/, Streamlit, and `st.session_state` for chat memory. Filing sections go straight into the prompt because they fit in the context window.

Prompt given to T1:

```
Rescope to a quick MVP. This overrides the CLAUDE.md stack. Open a small PR that updates the CLAUDE.md Conventions section to match; I will approve it by hand.

MVP stack: Python, LangGraph with 4 nodes (fetch -> validate -> summarize -> render), Claude through Portkey via agents/llm.py, yfinance, SEC EDGAR submissions API, files in out/<TICKER>/ (gitignored), Streamlit. Removed: Chroma, OpenAI embeddings, rag/, checkpointer, DeepEval, Railway, static HTML. Contract: agents/graph.py exposes run_pipeline(ticker: str) -> dict and answer(question: str, ticker: str, history: list) -> dict.

Close the issues that no longer apply, keep the skeleton. Backlog:
A. Fetch agent (tools/, agents/fetch.py, tests/test_fetch.py)
B. Validate and summarize (agents/validate.py, agents/summarize.py, tests/test_validate.py)
C. Render and app (app/, agents/graph.py, tests/test_app.py)

Plan A, B and C, then implement them in worktree-parallel mode.
```

Prompt given to T2: finish the filings corpus with AAPL, NVDA and JPM, skip the golden set, then write BEFORE_AFTER.md, DEMO.md and SLIDE.md on a side-slide branch.

Panel line for "why no vector database": one company's briefing sections fit in the context window, so retrieval adds moving parts without improving the answer. A vector store is the next step at hundreds of names or full filing history.

## 6. Lost terminals after a VS Code folder change

**User:** Changed folder in VScode and can't find my claude terminals, HELP

**User:** Where is T1, I only see T2

**User:** I need to find HOW i retrieve my T1, how do restart Claude and go back to history. what you gave me only goes to T2

**Claude:** Sessions are stored per folder. Found T1 by searching the session files for text only T1 had seen:

```bash
grep -l "Rescope to a quick MVP" ~/.claude/projects/*/*.jsonl
```

**User:** (result) /Users/eliaskruger_new/.claude/projects/-Users-eliaskruger-new-Projects-fde-interview/cc32b913-688c-49f7-863a-b3af9e6dba0c.jsonl

**Claude:** The underscore in the username also became a dash. Resume with:

```bash
cd /Users/eliaskruger_new/Projects/fde-interview
source .venv/bin/activate
claude --resume cc32b913-688c-49f7-863a-b3af9e6dba0c
```

Lesson: changing the VS Code folder reloads the window and kills its terminals. `claude --continue` only finds sessions for the current folder, and grepping `~/.claude/projects/` for a known phrase finds any session.

## 7. Pitch slide

**User:** Go to FDE-interview folder, in Docs look for slide and start building the slide here for me to present

**Claude:** Read docs/SLIDE.md and built a one-slide deck (Slides artifact "Advisor Stock Briefing Assistant"). Headline: "Brief an advisor on any stock in minutes, not an afternoon." Four-step flow with AI agent steps (Fetch, Summarize) in blue and plain-code steps (Validate, Render) in orange; then the problem, why you can trust it, and next 30 days. Footer covers the tickers, the stack and the "not investment advice" line, and the speaker notes hold a 30-second talk track. Changed "analysts" to "advisors" to match the scenario.

## 8. Dashboard sketch

**User:** Ok, now take a look at the demo.md and skethc out a html of how this would look like for the Wealth advisor

**Claude:** Built an HTML sketch ("Advisor Stock Briefing: Dashboard Sketch") following docs/DEMO.md, with a switcher for three states: AAPL ready (green status strip, quote card, cited briefing, chat with the follow-up, memory turn and buy-or-sell refusal), TSLA failing validation, and JPM needing a person after 3 refused fetches. Also gave T1 a prompt to restyle app/main.py to match.

**User:** Can you add synthetic data so it doesn look so tentative?

**Claude:** Filled the briefing with real figures from the AAPL 10-K in data/ (net sales $478.8B up 15%, iPhone $254.1B up 21%, gross margin 48.8% up from 46.9%, risks from Item 1A, drivers from Item 7). The quote is labeled sample data ($271.40, +0.80%, $4.03T market cap, P/E 33.6).

## 9. Save this history

**User:** Put this chat in the file in the AI history folder in the github repo

**Claude:** No ai-history folder existed, so created `ai-history/` at the repo root with this file.
