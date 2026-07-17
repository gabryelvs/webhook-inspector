from app.db import SessionLocal
from app.models import Bin


def test_bin_model_roundtrip(client):
    db = SessionLocal()
    try:
        b = Bin()
        db.add(b)
        db.commit()
        db.refresh(b)
        assert len(b.id) == 32
        assert b.created_at is not None
        assert b.name is None
    finally:
        db.close()
