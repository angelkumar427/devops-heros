from decimal import Decimal

import pytest
from sqlalchemy import text


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_when_schema_is_migrated(client):
    r = client.get("/ready")
    assert r.status_code == 200 and r.json()["status"] == "ready"


def test_migrations_reach_head():
    from app.db import engine
    with engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"


def test_create_and_get_product(client, make_product):
    p = make_product(unit_price="4.5")
    assert p["sku"] == "SKU-1" and p["quantity"] == 25 and p["low_stock"] is False
    assert p["unit_price"] == "4.50"  # the response shows what was stored, not what was sent
    r = client.get(f"/api/products/{p['id']}")
    assert r.status_code == 200 and r.json()["name"] == "USB-C cable"


def test_get_missing_product_returns_404(client):
    assert client.get("/api/products/999").status_code == 404


def test_duplicate_sku_is_rejected(client, make_product):
    make_product(sku="DUP-1")
    r = client.post("/api/products", json={"sku": "DUP-1", "name": "Other", "category": "X", "unit_price": "1"})
    assert r.status_code == 409


@pytest.mark.parametrize("payload", [
    {"sku": "BAD-1", "name": "Neg price", "category": "X", "unit_price": "-1"},
    {"sku": "bad lower", "name": "Bad SKU", "category": "X", "unit_price": "1"},
    {"sku": "BAD-2", "name": "", "category": "X", "unit_price": "1"},
    {"sku": "BAD-3", "name": "Neg qty", "category": "X", "unit_price": "1", "quantity": -5},
])
def test_invalid_products_are_rejected(client, payload):
    assert client.post("/api/products", json=payload).status_code == 422


def test_list_filters_by_category_low_stock_and_search(client, make_product):
    make_product(sku="CAB-1", name="HDMI cable", category="Cables", quantity=3, reorder_level=5)
    make_product(sku="CAB-2", name="USB cable", category="Cables", quantity=50)
    make_product(sku="KEY-1", name="Keyboard", category="Peripherals", quantity=30)
    assert len(client.get("/api/products").json()) == 3
    assert {p["sku"] for p in client.get("/api/products", params={"category": "Cables"}).json()} == {"CAB-1", "CAB-2"}
    assert [p["sku"] for p in client.get("/api/products", params={"low_stock": True}).json()] == ["CAB-1"]
    assert [p["sku"] for p in client.get("/api/products", params={"q": "key"}).json()] == ["KEY-1"]


def test_update_product(client, make_product):
    p = make_product()
    r = client.put(f"/api/products/{p['id']}",
                   json={"name": "USB-C cable 2m", "category": "Cables", "reorder_level": 30, "unit_price": "5.25"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "USB-C cable 2m" and Decimal(body["unit_price"]) == Decimal("5.25")
    assert body["low_stock"] is True  # 25 on hand is now below the new reorder level of 30
    assert body["quantity"] == 25     # PUT never touches stock - that is audited via /adjust


def test_update_missing_product_returns_404(client):
    r = client.put("/api/products/999", json={"name": "x", "category": "x", "reorder_level": 1, "unit_price": "1"})
    assert r.status_code == 404


def test_delete_product_and_its_history(client, make_product):
    p = make_product()
    assert client.delete(f"/api/products/{p['id']}").status_code == 204
    assert client.get(f"/api/products/{p['id']}").status_code == 404
    assert client.get("/api/movements").json() == []  # opening-stock movement removed with it


def test_adjust_stock_records_a_movement(client, make_product):
    p = make_product(quantity=10)
    r = client.post(f"/api/products/{p['id']}/adjust", json={"change": 15, "reason": "PO-1042 received"})
    assert r.status_code == 200 and r.json()["quantity"] == 25
    r = client.post(f"/api/products/{p['id']}/adjust", json={"change": -20, "reason": "order #88"})
    assert r.json()["quantity"] == 5 and r.json()["low_stock"] is True
    moves = client.get("/api/movements").json()
    assert [(m["change"], m["quantity_after"]) for m in moves] == [(-20, 5), (15, 25), (10, 10)]


def test_adjust_cannot_take_stock_below_zero(client, make_product):
    p = make_product(quantity=4)
    r = client.post(f"/api/products/{p['id']}/adjust", json={"change": -5, "reason": "order #9"})
    assert r.status_code == 409
    assert client.get(f"/api/products/{p['id']}").json()["quantity"] == 4


def test_adjust_rejects_zero_change(client, make_product):
    p = make_product()
    assert client.post(f"/api/products/{p['id']}/adjust", json={"change": 0, "reason": "noop"}).status_code == 422


def test_stats(client, make_product):
    make_product(sku="A-1", category="Cables", quantity=10, reorder_level=5, unit_price="2.50")  # 25.00
    make_product(sku="A-2", category="Cables", quantity=0, reorder_level=5, unit_price="9")  # out of stock
    make_product(sku="B-1", category="Audio", quantity=4, reorder_level=5, unit_price="20")  # 80.00, low
    s = client.get("/api/stats").json()
    assert s["total_products"] == 3 and s["total_units"] == 14
    assert Decimal(s["inventory_value"]) == Decimal("105.00")
    assert s["low_stock"] == 2 and s["out_of_stock"] == 1
    assert [c["category"] for c in s["by_category"]] == ["Audio", "Cables"]


def test_metrics_expose_http_and_inventory_gauges(client, make_product):
    make_product(quantity=7)
    client.get("/api/products")
    body = client.get("/metrics").text
    assert 'http_requests_total{handler="/api/products",method="GET",status="2xx"}' in body
    # millisecond buckets, so p95 latency is measured rather than interpolated
    assert 'http_request_duration_seconds_bucket{handler="/api/products",le="0.005",method="GET"}' in body
    assert "inventory_products 1.0" in body
    assert "inventory_units 7.0" in body


def test_database_url_built_from_parts_escapes_the_password(monkeypatch):
    """Kubernetes passes user/password/host separately; special characters must be URL-escaped."""
    from app.config import database_url
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss/w:rd")
    monkeypatch.setenv("POSTGRES_HOST", "db")
    assert database_url() == "postgresql+psycopg://stockpilot:p%40ss%2Fw%3Ard@db:5432/stockpilot"
