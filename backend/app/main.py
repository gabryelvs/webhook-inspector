from fastapi import FastAPI

from app.db import init_db
from app.routers import bins, capture


def create_app() -> FastAPI:
    app = FastAPI(title="Webhook Inspector")
    init_db()
    app.include_router(bins.router)
    app.include_router(capture.router)

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
