"""Business metrics, computed from the database at scrape time.

Reading the DB on scrape (instead of updating gauges on write) means every replica reports the
same, correct numbers - including a pod that has just started and has not served a write yet.
"""
import logging

from prometheus_client.core import REGISTRY, GaugeMetricFamily
from sqlalchemy import func, select

log = logging.getLogger("stockpilot.metrics")


class InventoryCollector:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    def collect(self):
        from .models import Product  # local import avoids a cycle at module load

        products = GaugeMetricFamily("inventory_products", "Number of products in the catalogue")
        units = GaugeMetricFamily("inventory_units", "Total units in stock")
        value = GaugeMetricFamily("inventory_value", "Total stock value (quantity x unit price)")
        low = GaugeMetricFamily("inventory_low_stock_products", "Products at or below their reorder level")
        try:
            with self._session_factory() as db:
                n, u, v = db.execute(select(
                    func.count(Product.id), func.coalesce(func.sum(Product.quantity), 0),
                    func.coalesce(func.sum(Product.quantity * Product.unit_price), 0))).one()
                lo = db.scalar(select(func.count()).where(Product.quantity <= Product.reorder_level)) or 0
        except Exception:  # noqa: BLE001 - a DB outage must not break the whole /metrics scrape
            log.warning("inventory metrics unavailable: database not reachable")
            return
        products.add_metric([], n)
        units.add_metric([], u)
        value.add_metric([], float(v))
        low.add_metric([], lo)
        yield from (products, units, value, low)


_registered = False


def register(session_factory):
    global _registered
    if not _registered:
        REGISTRY.register(InventoryCollector(session_factory))
        _registered = True
