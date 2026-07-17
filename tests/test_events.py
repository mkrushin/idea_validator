def test_track_visit_writes_event(client):
    r = client.post("/api/track", json={"session_id": "s1", "event_type": "visit"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_track_rejects_unknown_event_type(client):
    r = client.post("/api/track", json={"session_id": "s1", "event_type": "analysis_run"})
    assert r.status_code == 422  # analysis_run пишет только бэкенд


def test_count_events_today(client):
    client.post("/api/track", json={"session_id": "s1", "event_type": "visit"})
    client.post("/api/track", json={"session_id": "s2", "event_type": "visit"})
    client.post("/api/track", json={"session_id": "s1", "event_type": "cta_click"})

    import db
    assert db.count_events_today("visit") == 2
    assert db.count_events_today("cta_click") == 1
    assert db.count_events_today("visit", session_id="s1") == 1
