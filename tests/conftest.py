"""Hermetic test fixtures: SQLite + no external services + no API keys.

TESTING=1 must be set BEFORE the app is imported so database/config.py picks SQLite.
"""
import os
import sys
import pathlib

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///./test.db")

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    # Fresh DB per test session.
    db_file = pathlib.Path("test.db")
    if db_file.exists():
        db_file.unlink()
    from backend.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_token(client):
    r = client.post("/api/auth/register", json={"email": "t@example.com", "password": "secret123"})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
