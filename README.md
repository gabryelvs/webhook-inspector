# Webhook Inspector

**Live demo:** https://webhook-inspector-gv.fly.dev

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
- Single-container deploy: FastAPI serves the built React app

## Stack

FastAPI · SQLAlchemy · PostgreSQL · React · TypeScript · Vite · Tailwind ·
pytest · Vitest · Docker

## Run it

    docker compose up --build

Open http://localhost:8000, create a bin, then:

    curl -X POST http://localhost:8000/in/<bin-id>/test -d '{"hello":1}' -H "Content-Type: application/json"

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

## Roadmap

- v0.2 — WebSocket live-tail (replace polling), UI polish
- v0.3 — replay captured requests to a target URL, delete, demo GIF
- Later — auth, named bins, custom responses per bin
