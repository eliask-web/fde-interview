#!/usr/bin/env bash
# One-command setup for a fresh repo made from this template.
# Creates the virtual environment, installs packages, copies your keys
# from an existing .env without printing them, and runs the preflight.
#
# Usage, from the new repo's folder:
#   bash scripts/bootstrap.sh ~/Projects/fde-prototype-dryrun/.env

set -euo pipefail

ENV_SOURCE="${1:-$HOME/Projects/fde-prototype-dryrun/.env}"

if ! command -v python3.12 >/dev/null 2>&1; then
  echo "python3.12 not found. Run: brew install python@3.12"
  exit 1
fi

if [ ! -f "$ENV_SOURCE" ]; then
  echo "No .env found at $ENV_SOURCE"
  echo "Pass the path to a working .env, for example:"
  echo "  bash scripts/bootstrap.sh ~/Projects/fde-prototype-dryrun/.env"
  exit 1
fi

echo "1/4 Creating the virtual environment"
[ -d .venv ] || python3.12 -m venv .venv

echo "2/4 Installing packages (a few minutes)"
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

echo "3/4 Copying your keys into .env (not shown)"
cp "$ENV_SOURCE" .env
chmod 600 .env

echo "4/4 Running the preflight"
.venv/bin/python scripts/preflight.py

echo
echo "Done. Next:"
echo "  source .venv/bin/activate"
echo "  claude    then type: Run harness-setup."
