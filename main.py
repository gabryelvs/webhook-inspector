"""Vercel serverless entrypoint.

Vercel's Python runtime looks for a FastAPI `app` in `main.py` (or `app.py`,
`index.py`, `server.py`) at the repo root. The real application lives in
backend/app/main.py, and its modules import as `from app.x import ...` with
backend/ as their root. Putting backend/ on sys.path here lets those imports
resolve unchanged — nothing under backend/ needs to know it's deployed to
Vercel rather than run via `uvicorn app.main:app` from backend/ (Dockerfile)
or backend/ directly (local dev).
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402 (import must follow the sys.path setup above)

__all__ = ["app"]
