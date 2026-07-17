def test_bin_creation_rate_limited(client):
    for _ in range(10):
        res = client.post("/api/bins")
        assert res.status_code == 201

    res = client.post("/api/bins")
    assert res.status_code == 429
