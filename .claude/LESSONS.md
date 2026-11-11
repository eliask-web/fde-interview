# Project lessons for workflow subagents

Project-specific gotchas that the issue-planner and issue-implementer skills inject into every subagent prompt. This file belongs to this project. Append a dated entry whenever something bites: one to three lines, written as an instruction to a future agent.

- 2026-11-02: The harness's agent-boundary hook rejects an entire subagent Bash call if any `git` command text appears in it, even last in a `&&` chain, so earlier commands in that call never run. Keep git out of subagent Bash calls entirely.
- 2026-11-09: RAGAS fails to import with the current LangChain (`langchain_community.chat_models.vertexai` is gone). Use DeepEval for evaluation.
- 2026-11-09: Unit tests must not call Anthropic or OpenAI. Mock the model and the embeddings so the baseline stays fast, free and green.
- 2026-11-11: The trail-blazer push-guard hook blocks a whole Bash call containing a bare `git push` when `git switch main` appears in the same call. Push with an explicit `origin <branch>` in its own call.
