"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PricePointSchema(BaseModel):
    """Single price point in history."""

    scraped_at: datetime
    price: int
    avg_7d: Optional[int] = None
    avg_30d: Optional[int] = None


class ProductOutSchema(BaseModel):
    """Product response schema."""

    id: int
    name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    platform: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    current_price: Optional[int] = None
    original_price: Optional[int] = None
    discount_pct: Optional[float] = None
    deal_label: Optional[str] = None
    deal_confidence: Optional[float] = None


class ProductDetailOutSchema(ProductOutSchema):
    """Product with full price history."""

    history: list[PricePointSchema] = Field(default_factory=list)


class DealOutSchema(BaseModel):
    """Deal response schema."""

    id: int
    name: str
    platform: str
    current_price: int
    max_30d: int
    drop_pct: float
    url: Optional[str] = None
    image_url: Optional[str] = None
    reason: str


class AlertInSchema(BaseModel):
    """Price alert creation schema."""

    product_id: int
    target_price: int
    email: str


class AlertOutSchema(BaseModel):
    """Price alert response schema."""

    id: int
    product_id: int
    target_price: int
    email: str
    triggered: bool
    created_at: datetime


class KPISummarySchema(BaseModel):
    """KPI summary response schema."""

    total_products: int
    deals_today: int
    avg_discount_pct: float
    best_deal_name: Optional[str] = None
    best_deal_saving: int
    last_scraped_at: Optional[datetime] = None


class HealthSchema(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
