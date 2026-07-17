from datetime import datetime, timedelta, timezone

from app.db import SessionLocal
from app.models import Bin, CapturedRequest


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


def test_create_bin(client):
    res = client.post("/api/bins")
    assert res.status_code == 201
    data = res.json()
    assert len(data["id"]) == 32
    assert data["name"] is None
    assert "created_at" in data


def test_get_bin(client):
    bin_id = client.post("/api/bins").json()["id"]
    res = client.get(f"/api/bins/{bin_id}")
    assert res.status_code == 200
    assert res.json()["id"] == bin_id


def test_get_bin_404(client):
    res = client.get("/api/bins/doesnotexist")
    assert res.status_code == 404
    assert res.json() == {"detail": "bin not found"}


def test_old_bins_expire_on_create(client):
    old_bin_id = client.post("/api/bins").json()["id"]

    db = SessionLocal()
    try:
        old_bin = db.get(Bin, old_bin_id)
        old_bin.created_at = datetime.now(timezone.utc) - timedelta(days=8)
        db.add(CapturedRequest(bin_id=old_bin_id, method="GET", path="/"))
        db.commit()
    finally:
        db.close()

    res = client.post("/api/bins")
    assert res.status_code == 201
    new_bin_id = res.json()["id"]

    db = SessionLocal()
    try:
        assert db.get(Bin, old_bin_id) is None
        assert (
            db.query(CapturedRequest)
            .filter(CapturedRequest.bin_id == old_bin_id)
            .count()
            == 0
        )
        assert db.get(Bin, new_bin_id) is not None
    finally:
        db.close()


def test_bin_creation_survives_ttl_cleanup_failure(client, monkeypatch):
    from app.routers import bins as bins_mod

    def boom(db):
        raise RuntimeError("cleanup exploded")

    monkeypatch.setattr(bins_mod, "_expire_old_bins", boom)
    res = client.post("/api/bins")
    assert res.status_code == 201
