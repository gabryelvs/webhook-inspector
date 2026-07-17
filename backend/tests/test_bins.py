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
