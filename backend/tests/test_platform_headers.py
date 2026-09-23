from app.db import SessionLocal
from app.models import CapturedRequest
from app.platform_headers import strip_platform_headers


def _make_bin(client) -> str:
    return client.post("/api/bins").json()["id"]


def _stored_headers(bin_id: str) -> dict:
    db = SessionLocal()
    try:
        row = db.query(CapturedRequest).filter(CapturedRequest.bin_id == bin_id).one()
        return row.headers
    finally:
        db.close()


VERCEL_ADDED = {
    "x-vercel-id": "lhr1::abc",
    "x-vercel-ip-city": "Canary%20Wharf",
    "x-vercel-ip-latitude": "51.5064",
    "x-real-ip": "203.0.113.7",
    "x-forwarded-for": "203.0.113.7",
    "x-forwarded-host": "example.vercel.app",
    "x-forwarded-proto": "https",
    "forwarded": "for=203.0.113.7;proto=https",
}


def test_strips_vercel_added_headers_on_vercel():
    kept = strip_platform_headers({**VERCEL_ADDED, "x-demo": "yes", "content-type": "application/json"}, on_vercel=True)
    assert kept == {"x-demo": "yes", "content-type": "application/json"}


def test_keeps_every_header_off_vercel():
    # Off Vercel these are just headers the sender chose to send, so they are shown as sent.
    headers = {**VERCEL_ADDED, "x-demo": "yes"}
    assert strip_platform_headers(headers, on_vercel=False) == headers


def test_capture_on_vercel_stores_only_what_the_sender_sent(client, monkeypatch):
    bin_id = _make_bin(client)
    monkeypatch.setenv("VERCEL", "1")
    client.post(f"/in/{bin_id}/hook", json={"a": 1}, headers={**VERCEL_ADDED, "X-Demo": "yes"})
    stored = _stored_headers(bin_id)
    assert stored.get("x-demo") == "yes"
    assert not any(k.startswith("x-vercel-") for k in stored)
    assert "x-real-ip" not in stored and "x-forwarded-for" not in stored


def test_capture_on_vercel_still_records_the_real_client_ip(client, monkeypatch):
    bin_id = _make_bin(client)
    monkeypatch.setenv("VERCEL", "1")
    client.post(f"/in/{bin_id}/hook", headers={"x-real-ip": "203.0.113.7"})
    db = SessionLocal()
    try:
        row = db.query(CapturedRequest).filter(CapturedRequest.bin_id == bin_id).one()
        assert row.source_ip == "203.0.113.7"
    finally:
        db.close()
