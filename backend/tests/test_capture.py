from app.db import SessionLocal
from app.models import CapturedRequest


def _make_bin(client) -> str:
    return client.post("/api/bins").json()["id"]


def _stored(bin_id: str) -> list[CapturedRequest]:
    db = SessionLocal()
    try:
        return (
            db.query(CapturedRequest)
            .filter(CapturedRequest.bin_id == bin_id)
            .all()
        )
    finally:
        db.close()


def test_capture_post_json(client):
    bin_id = _make_bin(client)
    res = client.post(
        f"/in/{bin_id}/orders/hook?source=stripe",
        json={"event": "payment.succeeded"},
        headers={"X-Custom": "abc"},
    )
    assert res.status_code == 200
    assert res.json() == {"ok": True}

    reqs = _stored(bin_id)
    assert len(reqs) == 1
    r = reqs[0]
    assert r.method == "POST"
    assert r.path == "/orders/hook"
    assert r.query == {"source": "stripe"}
    assert r.headers["x-custom"] == "abc"
    assert '"payment.succeeded"' in r.body
    assert r.content_type == "application/json"
    assert r.truncated is False


def test_capture_root_path_and_get(client):
    bin_id = _make_bin(client)
    res = client.get(f"/in/{bin_id}")
    assert res.status_code == 200
    reqs = _stored(bin_id)
    assert len(reqs) == 1
    assert reqs[0].method == "GET"
    assert reqs[0].path == "/"
    assert reqs[0].body == ""


def test_capture_unknown_bin_404(client):
    res = client.post("/in/doesnotexist", json={})
    assert res.status_code == 404


def test_capture_truncates_large_body(client):
    bin_id = _make_bin(client)
    big = "x" * 1_000_001
    res = client.post(f"/in/{bin_id}", content=big)
    assert res.status_code == 200
    r = _stored(bin_id)[0]
    assert r.truncated is True
    assert len(r.body) == 1_000_000


def test_capture_truncates_long_content_type(client):
    bin_id = _make_bin(client)
    long_ct = "application/" + "x" * 300
    res = client.post(f"/in/{bin_id}", content="{}", headers={"Content-Type": long_ct})
    assert res.status_code == 200
    r = _stored(bin_id)[0]
    assert len(r.content_type) == 255


def test_capture_all_methods(client):
    bin_id = _make_bin(client)
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        res = client.request(method, f"/in/{bin_id}/x")
        assert res.status_code == 200
    assert len(_stored(bin_id)) == 5


def test_capture_returns_200_when_db_fails(client, monkeypatch):
    from sqlalchemy.orm import Session

    def boom(self, *args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(Session, "get", boom)
    res = client.post("/in/anything", json={})
    assert res.status_code == 200
    assert res.json() == {"ok": True}
