def _seed(client):
    # 4 визита (s1..s4), 2 анализа (s1,s2), 1 клик (s1), 1 email (s1)
    for s in ["s1", "s2", "s3", "s4"]:
        client.post("/api/track", json={"session_id": s, "event_type": "visit"})
    idea = "Платформа онлайн-курсов по программированию с менторами и проверкой домашних заданий на практике"
    client.post("/api/analyze", json={"idea": idea, "session_id": "s1"})
    client.post("/api/analyze", json={"idea": idea, "session_id": "s2"})
    client.post("/api/track", json={"session_id": "s1", "event_type": "cta_click"})
    client.post("/api/waitlist", json={"email": "s1@x.com", "session_id": "s1"})


def test_stats_requires_token(client):
    assert client.get("/stats").status_code == 403
    assert client.get("/stats?token=wrong").status_code == 403


def test_stats_aggregates(client):
    _seed(client)
    r = client.get("/stats?token=test-token")
    assert r.status_code == 200
    d = r.json()
    assert d["visits"] == 4
    assert d["analyses"] == 2
    assert d["activation_pct"] == 50.0   # 2/4
    assert d["cta_ctr_pct"] == 50.0      # 1/2
    assert d["emails"] == 1
    assert "return_7d_pct" in d
