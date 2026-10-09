"""StockPilot - inventory management API."""
import logging

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator import metrics as http_metrics
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import metrics
from .config import APP_ENV, APP_VERSION, CORS_ORIGINS
from .db import SessionLocal, get_db
from .models import Product, StockMovement
from .schemas import (CategoryStat, MovementOut, ProductCreate, ProductOut, ProductUpdate, Stats,
                      StockAdjust)

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}')
log = logging.getLogger("stockpilot")

app = FastAPI(title="StockPilot API", version=APP_VERSION,
              description="Inventory management: products, stock movements and stock KPIs.")
if CORS_ORIGINS:
    app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

# HTTP request count + latency per route; business gauges are read from the DB at scrape time.
# The per-route histogram's default buckets are 0.1/0.5/1 s. This API answers in milliseconds, so
# every request would land in the first bucket and p95 would be a meaningless interpolation.
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).add(
    http_metrics.default(latency_lowr_buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5))
).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
metrics.register(SessionLocal)


def _get_or_404(db: Session, product_id: int, lock: bool = False) -> Product:
    stmt = select(Product).where(Product.id == product_id)
    if lock:
        stmt = stmt.with_for_update()  # serialise concurrent stock changes across replicas
    product = db.scalars(stmt).first()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"product {product_id} not found")
    return product


@app.get("/", include_in_schema=False)
def root():
    return {"service": "stockpilot-api", "env": APP_ENV, "version": APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["ops"])
def health():
    """Liveness: the process is up. Deliberately does not touch the database."""
    return {"status": "ok"}


@app.get("/ready", tags=["ops"])
def ready(response: Response, db: Session = Depends(get_db)):
    """Readiness: the database is reachable AND the schema has been migrated."""
    try:
        db.execute(text("SELECT 1 FROM products LIMIT 1"))
    except Exception as exc:  # noqa: BLE001 - any DB failure means "not ready"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not ready", "reason": type(exc).__name__}
    return {"status": "ready", "version": APP_VERSION}


@app.get("/api/products", response_model=list[ProductOut], tags=["products"])
def list_products(category: str | None = None, low_stock: bool | None = None,
                  q: str | None = Query(None, max_length=60), db: Session = Depends(get_db)):
    stmt = select(Product).order_by(Product.name)
    if category:
        stmt = stmt.where(Product.category == category)
    if low_stock is not None:
        cond = Product.quantity <= Product.reorder_level
        stmt = stmt.where(cond if low_stock else ~cond)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.sku.ilike(like)))
    return db.scalars(stmt).all()


@app.get("/api/products/{product_id}", response_model=ProductOut, tags=["products"])
def get_product(product_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, product_id)


@app.post("/api/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED, tags=["products"])
def create_product(body: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**body.model_dump())
    db.add(product)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, f"SKU {body.sku} already exists")
    if body.quantity:
        db.add(StockMovement(product_id=product.id, change=body.quantity, reason="opening stock",
                             quantity_after=body.quantity))
    db.commit()
    db.refresh(product)  # return what the database stored (e.g. price normalised to 2 dp)
    log.info("product created sku=%s", product.sku)
    return product


@app.put("/api/products/{product_id}", response_model=ProductOut, tags=["products"])
def update_product(product_id: int, body: ProductUpdate, db: Session = Depends(get_db)):
    product = _get_or_404(db, product_id)
    for field, value in body.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/api/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["products"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db.delete(_get_or_404(db, product_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/api/products/{product_id}/adjust", response_model=ProductOut, tags=["stock"])
def adjust_stock(product_id: int, body: StockAdjust, db: Session = Depends(get_db)):
    if body.change == 0:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "change must not be 0")
    product = _get_or_404(db, product_id, lock=True)
    new_qty = product.quantity + body.change
    if new_qty < 0:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"insufficient stock: {product.quantity} on hand, {-body.change} requested")
    product.quantity = new_qty
    db.add(StockMovement(product_id=product.id, change=body.change, reason=body.reason, quantity_after=new_qty))
    db.commit()
    db.refresh(product)
    return product


@app.get("/api/movements", response_model=list[MovementOut], tags=["stock"])
def list_movements(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.execute(
        select(StockMovement, Product.sku, Product.name)
        .join(Product).order_by(StockMovement.created_at.desc(), StockMovement.id.desc()).limit(limit)
    ).all()
    return [MovementOut(id=m.id, product_id=m.product_id, sku=sku, product_name=name, change=m.change,
                        reason=m.reason, quantity_after=m.quantity_after, created_at=m.created_at)
            for m, sku, name in rows]


@app.get("/api/stats", response_model=Stats, tags=["stock"])
def stats(db: Session = Depends(get_db)):
    value = func.coalesce(func.sum(Product.quantity * Product.unit_price), 0)
    total_products, total_units, inventory_value = db.execute(
        select(func.count(Product.id), func.coalesce(func.sum(Product.quantity), 0), value)).one()
    low = db.scalar(select(func.count()).where(Product.quantity <= Product.reorder_level)) or 0
    out = db.scalar(select(func.count()).where(Product.quantity == 0)) or 0
    by_cat = db.execute(
        select(Product.category, func.count(Product.id), func.coalesce(func.sum(Product.quantity), 0), value)
        .group_by(Product.category).order_by(Product.category)).all()
    return Stats(total_products=total_products, total_units=total_units, inventory_value=inventory_value,
                 low_stock=low, out_of_stock=out,
                 by_category=[CategoryStat(category=c, products=n, units=u, value=v) for c, n, u, v in by_cat])
