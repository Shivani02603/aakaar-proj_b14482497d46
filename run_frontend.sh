#!/usr/bin/env bash
# One-command frontend runner (macOS/Linux): installs deps on first run, starts Vite.
set -e
cd "$(dirname "$0")/frontend"
[ -d node_modules ] || { echo "Installing frontend dependencies..."; npm install --no-audit --no-fund; }
echo "Starting frontend on http://localhost:5173 ..."
exec npm run dev
