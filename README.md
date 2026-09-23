# Webhook Inspector

[![CI](https://github.com/gabryelvs/webhook-inspector/actions/workflows/ci.yml/badge.svg)](https://github.com/gabryelvs/webhook-inspector/actions/workflows/ci.yml)

**Live demo:** https://webhook-inspector-gv.vercel.app

Inspect, debug, and (soon) replay webhooks. Create a bin, point any webhook
at its URL, and watch requests arrive live in the browser.

Built as a fullstack companion to
[webhook-dispatcher](https://github.com/gabryelvs/webhook-dispatcher): one project sends webhooks
reliably, this one helps you debug them.

## Features (v0.1)

- Unique bin URLs — `POST /api/bins`, then send anything to `/in/{bin_id}/...`
- Captures method, path, headers, query, body (1 MB cap), source IP
- React UI: live request list (2 s polling), detail tabs (headers / body / query / raw)
- Retention: last 500 requests per bin
- Bin creation rate-limited to 10/min per client IP. The client IP comes from
  the deploy platform's own proxy header (`x-real-ip` on Vercel), never a
  client-supplied one; counters are in memory, per app instance
- FastAPI serves the built React app as static files

## Stack

FastAPI · SQLAlchemy · PostgreSQL (Neon) · React · TypeScript · Vite ·
Tailwind · pytest · Vitest · Docker · Vercel · GitHub Actions

## Run it

    docker compose up --build

Open http://localhost:8000, create a bin, then:

    curl -X POST http://localhost:8000/in/<bin-id>/test -d '{"hello":1}' -H "Content-Type: application/json"

## Deploy

Live on [Vercel](https://vercel.com) (the FastAPI app plus its built React
front end, served as one project) with [Neon](https://neon.tech) as the
Postgres database:

- Vercel discovers the FastAPI `app` from the root `main.py`, which puts
  `backend/` on `sys.path` and re-exports the app from
  `backend/app/main.py` unchanged. Runtime dependencies (no pytest/httpx)
  are declared in the root `pyproject.toml` and locked in `uv.lock`;
  `backend/requirements.txt` is unrelated to the deploy and keeps driving CI
  and local backend dev.
- `[tool.vercel.scripts].build` in `pyproject.toml` runs
  `scripts/vercel_build.sh`, which builds the front end and copies
  `frontend/dist` to `backend/static` — the same static-file layout the
  Dockerfile produces, so `main.py`'s `/assets` mount and SPA fallback need
  no changes.
- Set one environment variable in the Vercel project: `DATABASE_URL`, to
  Neon's **pooled** connection string (host contains `-pooler`). Tables are
  created automatically on start-up (`init_db()`); no separate migration
  step.
- `vercel.json` pins the framework preset to `fastapi` and the region to
  `lhr1` (London).

### Honest limits of the serverless deploy

- Vercel (Hobby) rejects request bodies over 4.5 MB before they reach the
  app, so the "the capture endpoint always returns 200" guarantee only holds
  up to that size — above it, the platform itself returns an error, not
  this app.
- The bin-creation rate limit is kept in memory per function instance.
  Serverless can spread requests across multiple warm instances (or cold-
  start a new one), so the same client can see a higher effective limit
  than the advertised 10/min — weaker than on a single long-lived container.
- The UI polls every 2 s; on Vercel each poll is a separate function
  invocation, not a persistent connection.
- Vercel adds its own request headers (`x-vercel-*`, which include the
  sender's approximate location, plus `x-real-ip` and `x-forwarded-*`). On
  Vercel these are removed before a request is stored, so a bin shows what
  the sender sent. Vercel overwrites `X-Forwarded-For` and `X-Real-IP`, so a
  sender's own values for those two can't be shown there.

## Development

Backend (http://localhost:8000):

    cd backend
    python -m venv .venv
    .venv/Scripts/pip install -r requirements.txt
    .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

Frontend dev server (http://localhost:5173, proxies /api and /in):

    cd frontend
    npm install
    npm run dev

Tests:

    cd backend && .venv/Scripts/python -m pytest
    cd frontend && npm test

CI (GitHub Actions, `.github/workflows/ci.yml`) runs on every pull request and
push to master: pytest for the backend; lint, Vitest and a typechecked
production build for the frontend.

## Roadmap

- v0.2 — WebSocket live-tail (replace polling), UI polish
- v0.3 — replay captured requests to a target URL, delete, demo GIF
- Later — auth, named bins, custom responses per bin
