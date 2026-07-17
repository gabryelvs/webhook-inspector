def _make_bin(client) -> str:
    return client.post("/api/bins").json()["id"]


def test_list_requests_newest_first(client):
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}/first")
    client.post(f"/in/{bin_id}/second")

    res = client.get(f"/api/bins/{bin_id}/requests")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["path"] == "/second"
    assert data[1]["path"] == "/first"


def test_list_requests_unknown_bin_404(client):
    res = client.get("/api/bins/doesnotexist/requests")
    assert res.status_code == 404


def test_list_requests_limit_offset(client):
    bin_id = _make_bin(client)
    for i in range(5):
        client.post(f"/in/{bin_id}/r{i}")
    res = client.get(f"/api/bins/{bin_id}/requests?limit=2&offset=1")
    data = res.json()
    assert len(data) == 2
    assert data[0]["path"] == "/r3"


def test_get_request(client):
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}/x", json={"a": 1})
    req_id = client.get(f"/api/bins/{bin_id}/requests").json()[0]["id"]

    res = client.get(f"/api/requests/{req_id}")
    assert res.status_code == 200
    assert res.json()["path"] == "/x"

    assert client.get("/api/requests/nope").status_code == 404


def test_delete_request(client):
    bin_id = _make_bin(client)
    client.post(f"/in/{bin_id}/x")
    req_id = client.get(f"/api/bins/{bin_id}/requests").json()[0]["id"]

    assert client.delete(f"/api/requests/{req_id}").status_code == 204
    assert client.get(f"/api/requests/{req_id}").status_code == 404
    assert client.delete("/api/requests/nope").status_code == 404


def test_prune_keeps_last_500(client, monkeypatch):
    from app.routers import capture as capture_mod

    monkeypatch.setattr(capture_mod, "MAX_REQUESTS_PER_BIN", 3)
    bin_id = _make_bin(client)
    for i in range(5):
        client.post(f"/in/{bin_id}/r{i}")

    data = client.get(f"/api/bins/{bin_id}/requests").json()
    assert len(data) == 3
    assert data[0]["path"] == "/r4"
    assert data[-1]["path"] == "/r2"
