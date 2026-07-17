import os
import sys
import tempfile
import importlib
import pytest
from fastapi.testclient import TestClient

# backend/ импортируется как top-level модули (db, main, claude_api) —
# так же, как это делает сам backend/main.py через sys.path.insert.
BACKEND = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


@pytest.fixture
def client(monkeypatch):
    """TestClient с изолированной временной БД, гарантированно demo-режим."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_PATH", path)
    monkeypatch.setenv("STATS_TOKEN", "test-token")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    import db
    import claude_api
    import main
    importlib.reload(db)
    importlib.reload(main)
    # Форсим demo независимо от локального .env (иначе эндпоинт-тесты пойдут в живой API)
    monkeypatch.setattr(claude_api, "client", None, raising=False)

    with TestClient(main.app) as c:
        yield c

    os.remove(path)
