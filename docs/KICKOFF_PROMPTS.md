# Session script

What to say at each stage of the 2.5 hours, in two Claude Code windows. Edit the bracketed parts. Talk out loud the whole time: the hiring manager reads the transcript.

- **Main window (T1):** runs the harness. It plans, builds and reviews the six issues through GitHub.
- **Side window (T2):** a second Claude Code in its own copy of the repo, on its own branches. It does work the harness does not own: the golden set, the demo script, the deploy setup, and PR reviews. It never edits a folder an open issue owns.

## 0 to 5 minutes: open the side window

In T2, from the repo folder:

```bash
source .venv/bin/activate
git worktree add ../$(basename "$PWD")-side -b side
cp .env ../$(basename "$PWD")-side/.env
cd ../$(basename "$PWD")-side
claude
```

## 5 to 15 minutes: scenario to backlog

**Main window (T1):**

> Here is the scenario: [paste]. The user is [who] and their pain is [what]. Read CLAUDE.md and docs/RUBRIC_CHECKLIST.md. The stack and layout in CLAUDE.md are decided. Write docs/PROJECT-BRIEF.md in 15 lines or less, then create these GitHub issues, each with an "Affected areas" line naming its folders so they can run in parallel:
>
> 1. Walking skeleton: every module in the CLAUDE.md layout with its entry point stubbed to the contract, a Streamlit page that runs, and passing tests with the LLM mocked.
> 2. Retrieval: load and chunk data/, embed, Chroma, `retrieve()`, and rebuild the index at startup when chroma_db is missing. Affected areas: rag/, tests/test_rag.py.
> 3. Agents and tools: the LangGraph router, retriever agent, action agent with a real tool call, reviewer agent. Affected areas: agents/graph.py, agents/nodes.py, tools/, tests/test_agents.py.
> 4. Front end: chat tab with sources, and a plain-language before-and-after tab that shows docs/BEFORE_AFTER.md. Affected areas: app/, tests/test_app.py.
> 5. Guardrails and memory: input checks, grounded answers with citations, low-confidence handoff, checkpointer memory. Affected areas: agents/guardrails.py, agents/memory.py, tests/test_guardrails.py.
> 6. Evaluation runner: eval/run_eval.py runs every question in eval/golden_set.jsonl through `answer()` and scores it with DeepEval, printed as a table. The golden set itself comes from a separate PR. Affected areas: eval/run_eval.py, tests/test_eval.py.

**Side window (T2), at the same time:**

> Read CLAUDE.md, the scenario [or: docs/DRY_RUN_SCENARIO.md] and the files in data/. Do not touch agents/, app/, rag/, tools/ or tests/. Write eval/golden_set.jsonl: 10 questions a real user would ask, each with the expected answer and the source file it comes from, one JSON object per line. Include one question the data cannot answer. Commit it on this branch, push the branch, and open a PR.

Then push the brief yourself in T3. The harness is not allowed to push to `main`:

```bash
git add docs/PROJECT-BRIEF.md && git commit -m "Add project brief" && git push
```

## 15 to 35 minutes: walking skeleton

**Main window (T1):**

> Plan issue 1.

Read the plan out loud. If the auto-approval policy did not approve it, approve it in T3:

```bash
gh issue edit 1 --add-label plan-approved
```

> Implement issue 1.

**Side window (T2), while the skeleton builds:**

> Start a new branch from origin/main named side-demo. Write docs/BEFORE_AFTER.md: a plain-language before-and-after for the user in the scenario, with no technical words, under 150 words. Then write docs/DEMO.md: six demo questions in this order: a normal question with sources, one that needs the tool, a follow-up that needs memory, an off-topic question, a prompt-injection attempt, a question the data cannot answer. For each, the answer you expect. Push the branch and open a PR.

Merge each PR yourself in T3 (the harness never merges):

```bash
gh pr list
gh pr merge <n> --squash --delete-branch
```

**Main window (T1):**

> Run harness-setup.

This records the green baseline every later issue is measured against.

## 35 to 100 minutes: parallel build

**Main window (T1):**

> Plan issues 2, 3 and 4.

Approve any plan the policy did not approve, then:

> Implement issues 2, 3 and 4 in worktree-parallel mode.

**Side window (T2), while they build:**

> Start a new branch from origin/main named side-deploy. Prepare the Railway deploy without touching agents/, app/, rag/, tools/ or tests/: a railway.json at the repo root with the start command from CLAUDE.md, and docs/DEPLOY.md with the exact steps and the list of variables to set. Push the branch and open a PR.

Then, as each harness PR opens:

> Review PR <n> against its issue's plan and docs/RUBRIC_CHECKLIST.md. Do not change any files. Tell me in five lines what it does well and the most important risk.

Merge each PR as it opens, then:

> Plan and implement issues 5 and 6.

## 100 to 125 minutes: evaluate and deploy

Run the eval in T4: `python eval/run_eval.py`. Then deploy by hand, following docs/DEPLOY.md: create a Railway project from the GitHub repo, paste the keys (`pbcopy < .env` puts them on the clipboard without showing them), and open the URL.

## 125 to 150 minutes: demo and review

**Main window (T1):**

> Review the repo against docs/RUBRIC_CHECKLIST.md. For each item say pass or fail and name the file.

Demo from docs/DEMO.md, show the eval table and one LangSmith trace, and close on what you would build next.

## If the clock gets tight

Skip the planner for small fixes and say so out loud. The side window can make them on a branch:

> Start a new branch from origin/main named side-fix. [describe the two-line fix]. Push the branch and open a PR.
