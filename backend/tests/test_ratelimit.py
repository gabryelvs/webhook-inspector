def test_bin_creation_rate_limited(client):
    for _ in range(10):
        res = client.post("/api/bins")
        assert res.status_code == 201

    res = client.post("/api/bins")
    assert res.status_code == 429


def test_rate_limit_is_per_client_behind_proxy(client):
    # In production every request reaches the app from Fly's proxy, so the
    # socket peer is the same for all visitors (TestClient always connects as
    # "testclient"). Only Fly-Client-IP tells real clients apart.
    first = {"Fly-Client-IP": "203.0.113.1"}
    second = {"Fly-Client-IP": "198.51.100.2"}

    for _ in range(10):
        assert client.post("/api/bins", headers=first).status_code == 201
    assert client.post("/api/bins", headers=first).status_code == 429

    res = client.post("/api/bins", headers=second)
    assert res.status_code == 201


def test_rate_limit_ignores_spoofed_x_forwarded_for(client):
    # A client rotating X-Forwarded-For values must not get a fresh bucket.
    for i in range(10):
        res = client.post("/api/bins", headers={"X-Forwarded-For": f"192.0.2.{i}"})
        assert res.status_code == 201

    res = client.post("/api/bins", headers={"X-Forwarded-For": "192.0.2.99"})
    assert res.status_code == 429
