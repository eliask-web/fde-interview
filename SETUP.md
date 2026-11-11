# Setup: accounts, keys and tools

Do all of this before the dry run. It takes 30 to 45 minutes, mostly sign-ups and adding billing credits.

## 1. Anthropic API key (Claude for the prototype's agents)

Your Claude subscription runs Claude Code and the harness. The prototype itself calls Claude through the API, which is billed separately.

1. Go to console.anthropic.com and sign in with your work email.
2. Open Billing and add credits. $10 to $20 covers the dry run and Wednesday.
3. Open API Keys, create a key named `fde-prototype`, and copy it right away. It is shown only once.

## 2. OpenAI API key (embeddings)

1. Go to platform.openai.com and sign in.
2. Open Billing and add $5 to $10 in credits.
3. Open API keys, create a secret key, and copy it.

## 3. LangSmith key (tracing)

1. Go to smith.langchain.com and sign up for the free Developer plan.
2. Open Settings, then API Keys, and create a personal key.

## 4. GitHub CLI and jq

The harness drives GitHub through the `gh` command, and its scripts need `jq`.

```bash
brew install gh jq
gh auth login     # GitHub.com, HTTPS, log in with the browser
gh auth status    # should show you logged in
```

## 5. Claude Code and the harness plugin

1. Update Claude Code. The harness needs version 2.1.85 or newer, on your Pro or Max plan.
2. In any Claude Code session, install the plugin once per machine:

```
/plugin marketplace add msummer/trail-blazer-flow
/plugin install trail-blazer-flow@trail-blazer-flow
```

When you open a repo made from this template and trust the folder, its `.claude/settings.json` turns the plugin on. Automatic updates are off in this template, so the harness cannot change between the dry run and the interview.

## 6. Railway

1. At railway.com, upgrade your workspace to Pro in the workspace settings.
2. Install the CLI and log in:

```bash
brew install railway
railway login
```

## 7. Python and the repo

```bash
brew install python@3.12
gh repo clone eliask-web/<repo-name>
cd <repo-name>
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # paste your three keys into .env
python scripts/preflight.py
```

Every preflight line should say OK. Then, in Claude Code inside the repo:

> Run harness-setup.

It checks the plugin, the labels and CLAUDE.md. Before issue #1 merges there is no code, so it will report that the baseline is not recorded yet. That is expected.

## 8. Your screen

1. Open three terminal panes side by side (iTerm2 split panes, or the VS Code terminal split): one for Claude Code, one for `gh` and `git`, and one to run the app.
2. Turn on a Focus mode so notifications do not pop up on the recording.
3. Test screen sharing in a call with yourself, and make the terminal font large enough to read.
