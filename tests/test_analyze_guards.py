IDEA = "Мобильное приложение для трекинга привычек с ИИ-напоминаниями и аналитикой прогресса пользователя"


def test_analyze_writes_analysis_run_event(client):
    r = client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"})
    assert r.status_code == 200
    import db
    assert db.count_events_today("analysis_run", session_id="s1") == 1


def test_analyze_per_session_limit(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "DAILY_SESSION_LIMIT", 2)
    for _ in range(2):
        assert client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"}).status_code == 200
    # 3-й запрос той же сессии — мягкий отказ, без вызова анализа
    r = client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"})
    assert r.status_code == 429


def test_analyze_global_limit(client, monkeypatch):
    import main
    monkeypatch.setattr(main, "DAILY_GLOBAL_LIMIT", 1)
    assert client.post("/api/analyze", json={"idea": IDEA, "session_id": "s1"}).status_code == 200
    # другая сессия, но глобальный лимит исчерпан
    r = client.post("/api/analyze", json={"idea": IDEA, "session_id": "s2"})
    assert r.status_code == 429


def test_analyze_works_without_session_id(client):
    r = client.post("/api/analyze", json={"idea": IDEA})
    assert r.status_code == 200
