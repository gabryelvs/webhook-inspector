# Webhook Inspector — Design Spec

**Date:** 2026-07-15
**Status:** Approved (brainstorming complete)
**Goal:** First fullstack portfolio project. A webhook debugging tool (webhook.site / ngrok-inspector style) that pairs with the existing `webhook-dispatcher` project and doubles as a React learning path.

## Why this project

- Portfolio is currently backend-only (PayLedger, fx-service, webhook-dispatcher, taskboard-api). This adds the fullstack dimension.
- Dev tool: hiring managers are developers and have personally felt this pain — strong signal.
- Coherent story: "built a webhook dispatcher, then built the debugging tool for it."
- Frontend learning arc fits near-zero React experience: list view → detail view → live updates → replay. Each milestone introduces one new concept.

## Architecture

- **Backend:** FastAPI + PostgreSQL + WebSocket
- **Frontend:** React + Vite + TypeScript + Tailwind (TypeScript from day one)
- **Deploy:** Docker Compose locally; Railway or Fly.io for a public live demo
- **Location:** new directory `D:\Project\webhook-inspector` (own git repo)

### Core flow

1. User creates a "bin" → gets unique URL `https://app/in/{bin_id}`
2. Any HTTP request to that URL is captured: method, path, headers, query, body, content-type, source IP, timestamp
3. Stored in Postgres, pushed live to the browser via WebSocket
4. UI shows request list (live) + detail view
5. Replay button re-sends a captured request to a user-chosen target URL and shows the response

### Access model

No auth in v0.1. Bins are unguessable UUIDs — the URL is the secret (same model as webhook.site). Real auth is a later milestone.

## Components

### Backend (FastAPI)

- `bins` router — create bin, get bin metadata
- `capture` route — catch-all `ANY /in/{bin_id}/{path:path}`, stores the request
- `requests` router — list / get / delete captured requests (paginated)
- `replay` service — re-sends via httpx to target URL, stores response result
- `ws` endpoint — `/ws/{bin_id}`, pushes new-capture events to connected clients

### Data model (2 tables)

- `bins(id, created_at, name)`
- `requests(id, bin_id, method, path, headers jsonb, query jsonb, body text, content_type, source_ip, received_at, replay_result jsonb, truncated bool)`

Replay results embedded as jsonb on `requests` — no third table in v0.1.

### Frontend (React)

- `HomePage` — create-bin button → redirect to BinPage
- `BinPage` — main screen: left panel request list (live), right panel detail
- `RequestList` — rows with method badge, path, time; WebSocket appends on top
- `RequestDetail` — tabs: headers / body (pretty-printed JSON) / query / raw
- `ReplayPanel` — target URL input + send + response status/body display
- State: plain `useState` + one custom `useWebSocket` hook. No Redux/Zustand (YAGNI; simpler learning path).

### Limits

- Body cap 1 MB — truncate over, set `truncated: true`
- Retention: keep last 500 requests per bin, prune older

## Error handling

- Unknown `bin_id` → 404 JSON
- Body > 1 MB → store truncated, still return 200 to sender (never break the webhook sender)
- Replay target unreachable / timeout (5 s) → store error string; UI shows red badge
- WebSocket drop → hook auto-reconnects with backoff; on reconnect, refetch list so nothing is missed
- Capture route always returns 200 fast; persistence failure is logged, never surfaces as 500 to the sender

## Testing

- **Backend:** pytest — capture route (all methods, oversized body, unusual headers), replay (mock target with respx), WebSocket event emission
- **Frontend:** Vitest + React Testing Library — RequestList render/append, RequestDetail tabs, ReplayPanel submit. Deliberately light; the goal is learning FE testing, not exhaustive coverage.
- **E2E:** one Playwright happy path, milestone 3+, not v0.1

## Milestones

| Milestone | Scope |
|-----------|-------|
| v0.1 (~2 wk) | Capture + store + list + detail, **polling** (no WS yet), minimal UI, deployed |
| v0.2 | WebSocket live-tail, Tailwind polish, JSON pretty-print |
| v0.3 | Replay, delete/prune, README + demo GIF → CV-ready |
| Later | Auth, bin naming, E2E tests, response customization (custom status/body per bin) |

Polling-first in v0.1 is deliberate: ship before learning WebSockets, swap in v0.2. Every milestone is deployable and demoable — this counters the no-deadline risk of never shipping.
