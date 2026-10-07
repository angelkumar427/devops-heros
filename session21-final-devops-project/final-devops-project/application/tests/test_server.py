import importlib
import json

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("API_TOKEN", "test-token")
    monkeypatch.setenv("MAX_TASKS", "3")
    from app import server
    importlib.reload(server)
    server.app.config["TESTING"] = True
    return server.app.test_client()


AUTH = {"Authorization": "Bearer test-token"}


def test_healthz(client):
    assert client.get("/healthz").status_code == 200


def test_ready_when_configured(client):
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ready"


def test_not_ready_without_token(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("API_TOKEN", "")
    from app import server
    importlib.reload(server)
    resp = server.app.test_client().get("/readyz")
    assert resp.status_code == 503
    assert "API_TOKEN" in resp.get_json()["reason"]


def test_create_requires_token(client):
    assert client.post("/api/tasks", json={"title": "x"}).status_code == 401
    assert client.post("/api/tasks", json={"title": "x"}, headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_create_and_list_persists_to_disk(client, tmp_path):
    resp = client.post("/api/tasks", json={"title": "  deploy v2  "}, headers=AUTH)
    assert resp.status_code == 201
    assert resp.get_json() == {"id": 1, "title": "deploy v2", "done": False}
    assert client.get("/api/tasks").get_json()[0]["title"] == "deploy v2"
    assert (tmp_path / "tasks.json").exists()


@pytest.mark.parametrize("payload", [{}, {"title": ""}, {"title": "   "}, {"title": 7}])
def test_rejects_invalid_title(client, payload):
    assert client.post("/api/tasks", json=payload, headers=AUTH).status_code == 400


def test_enforces_max_tasks(client):
    for i in range(3):
        assert client.post("/api/tasks", json={"title": f"t{i}"}, headers=AUTH).status_code == 201
    assert client.post("/api/tasks", json={"title": "one too many"}, headers=AUTH).status_code == 409


def test_metrics_exposed(client):
    client.get("/healthz")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'tasks_http_requests_total{method="GET",path="/healthz",status="200"} 1.0' in body
    assert 'endpoint="' not in body  # would collide with Prometheus Operator's target label
    assert 'le="0.001"' in body  # sub-5ms buckets, so p95 is measured rather than interpolated


def test_tasks_stored_gauge_reflects_disk_after_restart(tmp_path, monkeypatch):
    (tmp_path / "tasks.json").write_text(json.dumps([{"id": 1, "title": "a", "done": False}] * 3))
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    from app import server

    importlib.reload(server)  # a "new pod" that has not written anything yet
    body = server.app.test_client().get("/metrics").get_data(as_text=True)
    assert "tasks_stored 3.0" in body


def test_concurrent_writers_do_not_lose_tasks(tmp_path, monkeypatch):
    """Separate processes (like gunicorn workers or replicas) sharing one volume."""
    import multiprocessing

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("API_TOKEN", "t")
    monkeypatch.setenv("MAX_TASKS", "1000")
    ctx = multiprocessing.get_context("fork")
    procs = [ctx.Process(target=_post_many, args=(str(tmp_path), 25)) for _ in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    stored = json.loads((tmp_path / "tasks.json").read_text())
    assert len(stored) == 100
    assert len({t["id"] for t in stored}) == 100


def _post_many(data_dir, n):
    import importlib

    from app import server

    importlib.reload(server)
    c = server.app.test_client()
    for i in range(n):
        assert c.post("/api/tasks", json={"title": f"t{i}"}, headers={"Authorization": "Bearer t"}).status_code == 201
