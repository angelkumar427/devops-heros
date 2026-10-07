import pytest

from app.server import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_add_endpoint(client):
    resp = client.get("/add?a=2&b=3")
    assert resp.status_code == 200
    assert resp.get_json()["result"] == 5


def test_divide_by_zero_is_400(client):
    resp = client.get("/divide?a=1&b=0")
    assert resp.status_code == 400
    assert "zero" in resp.get_json()["error"]


def test_unknown_operation_is_404(client):
    assert client.get("/power?a=2&b=3").status_code == 404


def test_missing_params_is_400(client):
    assert client.get("/add?a=2").status_code == 400
