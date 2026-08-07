import logging
import os
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./dev.db")
# Fly's `postgres attach` sets a postgres:// scheme; SQLAlchemy needs the driver-qualified form
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

connect_args: dict = {}
engine_kwargs: dict = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db(retries: int = 10, delay: float = 3.0) -> None:
    # The DB may still be waking from an idle stop when this app cold-starts;
    # crashing here puts the app in a restart loop, so wait for it instead.
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
