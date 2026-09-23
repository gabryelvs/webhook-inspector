from app.db import SessionLocal
from app.models import CapturedRequest


def _make_bin(client) -> str:
    return client.post("/api/bins").json()["id"]


def _source_ip(bin_id: str) -> str | None:
    db = SessionLocal()
    try:
        row = (
            db.query(CapturedRequest)
            .filter(CapturedRequest.bin_id == bin_id)
            .one()
        )
        return row.source_ip
    finally:
        db.close()


def test_uses_x_real_ip_on_vercel(client, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}", json={}, headers={"X-Real-Ip": "203.0.113.9"})
    assert _source_ip(bin_id) == "203.0.113.9"


def test_ignores_fly_client_ip_on_vercel(client, monkeypatch):
    # Fly-Client-IP is meaningless on Vercel: only the matching proxy's own
    # header (x-real-ip) is trusted there.
    monkeypatch.setenv("VERCEL", "1")
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}", json={}, headers={"Fly-Client-IP": "203.0.113.9"})
    assert _source_ip(bin_id) == "testclient"


def test_falls_back_to_socket_peer_on_vercel_without_header(client, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}", json={})
    assert _source_ip(bin_id) == "testclient"


def test_uses_fly_client_ip_off_vercel(client, monkeypatch):
    monkeypatch.delenv("VERCEL", raising=False)
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}", json={}, headers={"Fly-Client-IP": "198.51.100.2"})
    assert _source_ip(bin_id) == "198.51.100.2"


def test_ignores_spoofed_x_real_ip_off_vercel(client, monkeypatch):
    # x-real-ip is only meaningful behind Vercel's own proxy; off Vercel it's
    # attacker-controlled like any other client-supplied header.
    monkeypatch.delenv("VERCEL", raising=False)
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}", json={}, headers={"X-Real-Ip": "9.9.9.9"})
    assert _source_ip(bin_id) == "testclient"


def test_truncates_long_x_real_ip_on_vercel(client, monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    bin_id = _make_bin(client)
    long_ip = "2001:0db8:0000:0000:0000:ff00:0042:8329" * 2
    client.post(f"/in/{bin_id}", json={}, headers={"X-Real-Ip": long_ip})
    assert _source_ip(bin_id) == long_ip[:45]
