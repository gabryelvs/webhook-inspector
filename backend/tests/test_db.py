import pytest
from sqlalchemy.exc import OperationalError

from app import db as db_mod


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
