# FDE prototype harness template

A starting point for building an AI prototype live with Claude Code, on top of Mark Summer's trail-blazer-flow harness (github.com/msummer/trail-blazer-flow, MIT license). The harness turns each GitHub issue into a plan, an implementation, an independent review and a PR.

This template carries the workflow and the stack decisions. It contains no application code: the prototype is built live from the scenario.

## What is here

| Path | What it is |
|---|---|
| `.claude/LESSONS.md` | Gotchas the harness feeds to every subagent |
| `.claude/settings.json` | Turns on the trail-blazer-flow plugin and grants the permissions it needs. Automatic updates are off |
| `CLAUDE.md` | The contract the harness reads: stack, layout, module entry points, rules, verification commands, and the plan auto-approval policy |
| `SETUP.md` | Accounts, keys, the plugin install, and the environment |
| `docs/KICKOFF_PROMPTS.md` | What to say at each stage of a 2.5-hour session, including the seven-issue backlog |
| `docs/RUBRIC_CHECKLIST.md` | What the prototype must show before it is called done |
| `requirements.txt`, `.env.example` | Python packages and the keys to fill in |
| `scripts/bootstrap.sh` | One command to set up a fresh repo: environment, packages, keys and preflight |
| `scripts/preflight.py` | Checks packages, keys and APIs before the clock starts |

## Using it

1. On GitHub, click "Use this template" to create a new private repo.
2. Clone it, then run `bash scripts/bootstrap.sh ~/Projects/fde-prototype-dryrun/.env` from its folder. First time on a new machine, follow SETUP.md instead.
3. Open `docs/KICKOFF_PROMPTS.md` and start the clock.
