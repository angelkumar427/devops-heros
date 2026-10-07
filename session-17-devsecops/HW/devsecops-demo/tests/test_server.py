import pytest

from app import server


@pytest.fixture
def client():
    server.reset()
    server.app.config["TESTING"] = True
    return server.app.test_client()


def test_health(client):
    assert client.get("/health").get_json()["status"] == "ok"


def test_create_and_get_note(client):
    created = client.post("/notes", json={"text": "  buy milk  "})
    assert created.status_code == 201
    assert created.get_json() == {"id": 1, "text": "buy milk"}
    assert client.get("/notes/1").get_json()["text"] == "buy milk"


def test_list_notes(client):
    client.post("/notes", json={"text": "a"})
    client.post("/notes", json={"text": "b"})
    assert [n["text"] for n in client.get("/notes").get_json()] == ["a", "b"]


@pytest.mark.parametrize("payload", [{}, {"text": ""}, {"text": "   "}, {"text": 42}])
def test_rejects_invalid_text(client, payload):
    assert client.post("/notes", json=payload).status_code == 400


def test_rejects_oversized_note(client):
    assert client.post("/notes", json={"text": "x" * 501}).status_code == 400


def test_missing_note_is_404(client):
    resp = client.get("/notes/99")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "note not found"
