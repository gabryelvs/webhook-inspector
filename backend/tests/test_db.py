import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool

from app import db as db_mod


def test_normalize_database_url_rewrites_postgres_scheme():
    assert (
        db_mod.normalize_database_url("postgres://u:p@host/db")
        == "postgresql+psycopg2://u:p@host/db"
    )


def test_normalize_database_url_rewrites_postgresql_scheme():
    # Neon's pooled connection string (host contains "-pooler") uses this
    # scheme; psycopg2 is the installed driver, so it needs the qualifier too.
    assert (
        db_mod.normalize_database_url("postgresql://u:p@ep-foo-pooler.neon.tech/db")
        == "postgresql+psycopg2://u:p@ep-foo-pooler.neon.tech/db"
    )


def test_normalize_database_url_leaves_sqlite_untouched():
    assert db_mod.normalize_database_url("sqlite:///./dev.db") == "sqlite:///./dev.db"
    assert db_mod.normalize_database_url("sqlite://") == "sqlite://"


def test_normalize_database_url_leaves_already_qualified_url_untouched():
    url = "postgresql+psycopg2://u:p@host/db"
    assert db_mod.normalize_database_url(url) == url


def test_engine_kwargs_for_vercel_uses_nullpool():
    # Neon's pooled endpoint (PgBouncer, transaction mode) already pools
    # connections; SQLAlchemy's own pool would hold connections across
    # invocations that a fresh serverless instance won't reuse.
    assert db_mod.engine_kwargs_for(is_vercel=True) == {"poolclass": NullPool}


def test_engine_kwargs_for_non_vercel_is_empty():
    assert db_mod.engine_kwargs_for(is_vercel=False) == {}


def test_retry_schedule_on_vercel_fits_hobby_request_limit():
    retries, delay = db_mod.retry_schedule(is_vercel=True)
    assert retries == 3
    assert delay == 1.0
    # Total wait must clear Vercel Hobby's 10s per-request limit.
    assert (retries - 1) * delay < 10


def test_retry_schedule_off_vercel_keeps_longer_default():
    assert db_mod.retry_schedule(is_vercel=False) == (10, 3.0)


def test_init_db_uses_short_schedule_on_vercel(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setattr(db_mod.time, "sleep", lambda seconds: None)
    calls = {"n": 0}

    def always_down(bind):
        calls["n"] += 1
        raise OperationalError("conn", None, Exception("db down"))

    monkeypatch.setattr(db_mod.Base.metadata, "create_all", always_down)
    with pytest.raises(OperationalError):
        db_mod.init_db()
    assert calls["n"] == 3


def test_init_db_uses_long_schedule_off_vercel(monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setattr(db_mod.time, "sleep", lambda seconds: None)
    calls = {"n": 0}

    def always_down(bind):
        calls["n"] += 1
        raise OperationalError("conn", None, Exception("db down"))

    monkeypatch.setattr(db_mod.Base.metadata, "create_all", always_down)
    with pytest.raises(OperationalError):
        db_mod.init_db()
    assert calls["n"] == 10


def test_init_db_retries_until_db_ready(monkeypatch):
    calls = {"n": 0}

    def flaky(bind):
        calls["n"] += 1
        if calls["n"] < 3:
            raise OperationalError("conn", None, Exception("db waking"))

    monkeypatch.setattr(db_mod.Base.metadata, "create_all", flaky)
    db_mod.init_db(retries=5, delay=0)
    assert calls["n"] == 3


def test_init_db_raises_after_exhausted_retries(monkeypatch):
    def always_down(bind):
        raise OperationalError("conn", None, Exception("db down"))

    monkeypatch.setattr(db_mod.Base.metadata, "create_all", always_down)
    with pytest.raises(OperationalError):
        db_mod.init_db(retries=2, delay=0)
