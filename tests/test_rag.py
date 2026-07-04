"""Hermetic RAG acceptance test — no DB server, no API keys (FakeEmbedder + FakeLLM).
Covers the DocChat-class success criteria: upload → ingest → ask → cited answer →
history survives.
"""
import io


def _upload(client, auth_headers, text: str, name: str = "notes.txt"):
    return client.post(
        "/api/ai/upload",
        headers=auth_headers,
        files={"file": (name, io.BytesIO(text.encode()), "text/plain")},
    )


def test_upload_and_ingest(client, auth_headers):
    r = _upload(client, auth_headers, "The solar system has eight planets. " * 40)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["chunks_indexed"] >= 1
    assert body["document_id"]


def test_upload_requires_auth(client):
    r = client.post("/api/ai/upload", files={"file": ("a.txt", io.BytesIO(b"x"), "text/plain")})
    assert r.status_code == 401


def test_bad_extension_rejected(client, auth_headers):
    r = client.post(
        "/api/ai/upload", headers=auth_headers,
        files={"file": ("evil.exe", io.BytesIO(b"x"), "application/octet-stream")},
    )
    assert r.status_code == 400


def test_query_returns_cited_answer(client, auth_headers):
    _upload(client, auth_headers, "Jupiter is the largest planet in the solar system. " * 30,
            name="jupiter.txt")
    r = client.post("/api/ai/query", headers=auth_headers,
                    json={"question": "Which is the largest planet?"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "jupiter" in body["answer"].lower() or "planet" in body["answer"].lower()
    assert body["citations"], "answer must cite source chunks"
    assert body["session_id"]


def test_chat_history_persists(client, auth_headers):
    r = client.post("/api/ai/query", headers=auth_headers,
                    json={"question": "Tell me about planets"})
    session_id = r.json()["session_id"]

    sessions = client.get("/api/ai/sessions", headers=auth_headers).json()
    assert any(s["id"] == session_id for s in sessions)

    msgs = client.get(f"/api/ai/sessions/{session_id}/messages", headers=auth_headers).json()
    roles = [m["role"] for m in msgs]
    assert "user" in roles and "assistant" in roles


def test_stream_endpoint(client, auth_headers):
    r = client.post("/api/ai/stream", headers=auth_headers,
                    json={"question": "What do the documents say?"})
    assert r.status_code == 200
    assert "data:" in r.text
    assert "done" in r.text
