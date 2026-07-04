#!/usr/bin/env bash
# One-command backend runner (macOS/Linux). Creates venv, installs deps, starts the API.
set -e
cd "$(dirname "$0")"                       # always run from the project root

if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
./venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt

if [ ! -f .env ] && [ -z "$DATABASE_URL" ]; then
  echo "No .env found - starting in DEMO mode (SQLite, no keys needed)."
  echo "For real mode: cp .env.example .env and fill in your values."
  export TESTING=1
  export JWT_SECRET="${JWT_SECRET:-dev-demo-secret}"
fi

echo "Starting backend on http://localhost:8000 ..."
exec ./venv/bin/python -m uvicorn backend.main:app --port 8000
