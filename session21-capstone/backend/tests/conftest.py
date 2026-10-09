"""Test setup: a throwaway SQLite database, built by the real Alembic migrations.

DATABASE_URL is set before the app is imported, so the app (and its metrics collector) can
never reach a real Postgres during tests.
"""
import os
import pathlib
import tempfile

_TMP = tempfile.mkdtemp(prefix="stockpilot-test-")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_TMP}/test.db"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import text  # noqa: E402

BACKEND = pathlib.Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture
def client(migrated_db):
    from fastapi.testclient import TestClient

    from app.db import engine
    from app.main import app

    with engine.begin() as conn:  # every test starts from an empty catalogue
        conn.execute(text("DELETE FROM stock_movements"))
        conn.execute(text("DELETE FROM products"))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_product(client):
    def _make(sku="SKU-1", name="USB-C cable", category="Cables", quantity=25, reorder_level=10, unit_price="4.50"):
        r = client.post("/api/products", json={"sku": sku, "name": name, "category": category,
                                               "quantity": quantity, "reorder_level": reorder_level,
                                               "unit_price": unit_price})
        assert r.status_code == 201, r.text
        return r.json()
    return _make
