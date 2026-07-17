def test_waitlist_saves_email_and_logs_event(client):
    r = client.post("/api/waitlist", json={"email": "a@b.com", "session_id": "s1"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["already_joined"] is False

    import db
    assert db.count_events_today("email_submit", session_id="s1") == 1


def test_waitlist_duplicate_email_still_logs_event(client):
    client.post("/api/waitlist", json={"email": "a@b.com", "session_id": "s1"})
    r = client.post("/api/waitlist", json={"email": "a@b.com", "session_id": "s2"})
    assert r.status_code == 200
    assert r.json()["already_joined"] is True

    import db
    # Событие пишется при каждом submit (сигнал намерения), даже для дубля email
    assert db.count_events_today("email_submit") == 2


def test_waitlist_accepts_missing_session_id(client):
    r = client.post("/api/waitlist", json={"email": "c@d.com"})
    assert r.status_code == 200
