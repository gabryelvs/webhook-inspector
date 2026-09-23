#!/usr/bin/env bash
# Runs as [tool.vercel.scripts].build (pyproject.toml), after Vercel installs
# the root requirements.txt. Builds the React front end and copies it into
# backend/static, exactly like the Dockerfile's frontend build stage, so
# backend/app/main.py's existing StaticFiles mount and SPA fallback work
# unchanged — Vercel promotes that mount's files to its CDN at build time.
set -euo pipefail

cd "$(dirname "$0")/.."

(cd frontend && npm ci && npm run build)

rm -rf backend/static
cp -r frontend/dist backend/static
