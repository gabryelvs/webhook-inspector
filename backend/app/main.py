from fastapi import FastAPI

from app.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Webhook Inspector")
    init_db()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
