import logging
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.models import Base

logger = logging.getLogger(__name__)


def normalize_database_url(url: str) -> str:
    """Rewrite the scheme to the psycopg2-qualified form SQLAlchemy needs.

    Both Fly's `postgres attach` (postgres://) and Neon's pooled connection
    string (postgresql://, host containing "-pooler") hand out schemes that
    don't name a driver; the app uses psycopg2, so either needs the
    `+psycopg2` qualifier. sqlite URLs, and URLs that already name a driver,
    pass through untouched.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def engine_kwargs_for(is_vercel: bool) -> dict:
    """Extra create_engine() kwargs for non-sqlite databases.

    On Vercel each invocation may land on a fresh serverless instance, so
    SQLAlchemy's own connection pool buys little and can hold connections
    open in a way Neon's pooled endpoint (PgBouncer, transaction mode)
    doesn't expect long-lived clients to. NullPool opens a fresh connection
    per checkout and closes it on return, leaving all pooling to Neon's
    `-pooler` endpoint. psycopg2 doesn't prepare statements server-side by
    default, so PgBouncer transaction-mode pooling needs nothing else here.
    """
    if is_vercel:
        return {"poolclass": NullPool}
    return {}


def retry_schedule(is_vercel: bool) -> tuple[int, float]:
    """(retries, delay) for init_db's wait loop.

    Vercel's Hobby plan caps a request — and so a cold-start's init_db call —
    at 10s, so the default 10 attempts * 3s (up to 30s) would exceed it; use
    a short schedule that fits instead. Elsewhere (Docker/Fly) keep the
    longer schedule, since there a slow Postgres wake-up matters more than a
    fast failure.
    """
    if is_vercel:
        return 3, 1.0
    return 10, 3.0


DATABASE_URL = normalize_database_url(os.environ.get("DATABASE_URL", "sqlite:///./dev.db"))

connect_args: dict = {}
engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
        engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs.update(engine_kwargs_for(is_vercel=bool(os.environ.get("VERCEL"))))

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db(retries: int | None = None, delay: float | None = None) -> None:
    # The DB may still be waking from an idle stop when this app cold-starts;
    # crashing here puts the app in a restart loop, so wait for it instead.
    if retries is None or delay is None:
        default_retries, default_delay = retry_schedule(bool(os.environ.get("VERCEL")))
        if retries is None:
            retries = default_retries
        if delay is None:
            delay = default_delay

    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            return
        except OperationalError:
            if attempt == retries:
                raise
            logger.warning("database not ready (attempt %d/%d), retrying", attempt, retries)
            time.sleep(delay)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
