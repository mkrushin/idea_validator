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


def test_return_7d_zero_when_no_multiday_sessions(client):
    _seed(client)
    d = client.get("/stats?token=test-token").json()
    assert d["return_7d_pct"] == 0.0  # ни одна сессия не заходила в 2 разных дня


def test_return_7d_counts_multiday_session(client):
    import sqlite3
    import db
    conn = sqlite3.connect(db.get_db_path())
    cur = conn.cursor()
    # r1: визиты в 2 разных дня (вчера + сегодня, в пределах 7 дней) → возврат
    cur.execute("INSERT INTO events (session_id, event_type, created_at) VALUES ('r1','visit', datetime('now','-1 day'))")
    cur.execute("INSERT INTO events (session_id, event_type, created_at) VALUES ('r1','visit', datetime('now'))")
    # r2: визит только сегодня → не возврат
    cur.execute("INSERT INTO events (session_id, event_type, created_at) VALUES ('r2','visit', datetime('now'))")
    conn.commit()
    conn.close()
    d = client.get("/stats?token=test-token").json()
    assert d["visits"] == 2            # r1, r2
    assert d["return_7d_pct"] == 50.0  # 1 из 2 (r1) вернулся


def test_stats_reports_analyses_today(client):
    idea = "Сервис подбора книг по настроению с рекомендациями на основе прошлых оценок пользователя онлайн"
    client.post("/api/analyze", json={"idea": idea, "session_id": "a1"})
    d = client.get("/stats?token=test-token").json()
    assert d["analyses_today"] == 1


def test_stats_503_when_token_unset(client, monkeypatch):
    monkeypatch.delenv("STATS_TOKEN", raising=False)
    r = client.get("/stats?token=whatever")
    assert r.status_code == 503
