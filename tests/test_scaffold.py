"""Scaffold acceptance tests — these are green BEFORE any LLM writes a line.
They stay in the generated project so regressions in scaffold-owned code are caught too.
"""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["db"] is True


def test_register_returns_token(auth_token):
    assert isinstance(auth_token, str) and len(auth_token) > 20


def test_duplicate_register_rejected(client):
    r = client.post("/api/auth/register", json={"email": "t@example.com", "password": "secret123"})
    assert r.status_code == 400


def test_login_and_me(client):
    r = client.post("/api/auth/login", json={"email": "t@example.com", "password": "secret123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "t@example.com"


def test_wrong_password_401(client):
    r = client.post("/api/auth/login", json={"email": "t@example.com", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/auth/me").status_code == 401
