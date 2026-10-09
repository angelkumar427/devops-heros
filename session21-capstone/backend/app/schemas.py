from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=60)
    reorder_level: int = Field(default=10, ge=0)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class ProductCreate(ProductBase):
    sku: str = Field(min_length=2, max_length=32, pattern=r"^[A-Z0-9-]+$")
    quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    """PUT replaces the editable fields. Quantity changes go through /adjust so they are audited."""

    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=60)
    reorder_level: int = Field(ge=0)
    unit_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    quantity: int
    low_stock: bool
    created_at: datetime
    updated_at: datetime


class StockAdjust(BaseModel):
    change: int = Field(description="positive = stock received, negative = stock issued")
    reason: str = Field(min_length=1, max_length=120)


class MovementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    sku: str
    product_name: str
    change: int
    reason: str
    quantity_after: int
    created_at: datetime


class CategoryStat(BaseModel):
    category: str
    products: int
    units: int
    value: Decimal


class Stats(BaseModel):
    total_products: int
    total_units: int
    inventory_value: Decimal
    low_stock: int
    out_of_stock: int
    by_category: list[CategoryStat]
