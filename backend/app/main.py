from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.routers import bins, capture, requests as requests_router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Webhook Inspector")
    init_db()
    app.include_router(bins.router)
    app.include_router(requests_router.router)
    app.include_router(capture.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    if STATIC_DIR.exists():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
