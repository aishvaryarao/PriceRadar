"""Tests for FastAPI endpoints."""
import pytest
from datetime import datetime
from src.api.schemas import (
    ProductOutSchema,
    DealOutSchema,
    AlertInSchema,
    AlertOutSchema,
    KPISummarySchema,
    HealthSchema,
)


class TestSchemas:
    """Test Pydantic schemas."""

    def test_health_schema(self):
        """Test health schema."""
        health = HealthSchema(status="ok", timestamp=datetime.utcnow())
        assert health.status == "ok"
        assert isinstance(health.timestamp, datetime)

    def test_product_schema(self):
        """Test product schema."""
        product = ProductOutSchema(
            id=1,
            name="iPhone 15",
            platform="amazon",
            url="http://example.com",
            current_price=79999,
        )
        assert product.id == 1
        assert product.name == "iPhone 15"
        assert product.current_price == 79999

    def test_deal_schema(self):
        """Test deal schema."""
        deal = DealOutSchema(
            id=1,
            name="iPhone 15",
            platform="amazon",
            current_price=79999,
            max_30d=99999,
            drop_pct=20.0,
            url="http://example.com",
            reason="Price dropped 20%",
        )
        assert deal.drop_pct == 20.0
        assert deal.reason == "Price dropped 20%"

    def test_alert_schema_in(self):
        """Test alert input schema."""
        alert = AlertInSchema(product_id=1, target_price=50000, email="test@example.com")
        assert alert.product_id == 1
        assert alert.target_price == 50000

    def test_alert_schema_out(self):
        """Test alert output schema."""
        alert = AlertOutSchema(
            id=1,
            product_id=1,
            target_price=50000,
            email="test@example.com",
            triggered=False,
            created_at=datetime.utcnow(),
        )
        assert alert.triggered is False

    def test_kpi_schema(self):
        """Test KPI summary schema."""
        kpi = KPISummarySchema(
            total_products=100,
            deals_today=5,
            avg_discount_pct=15.5,
            best_deal_name="iPhone 15",
            best_deal_saving=20000,
        )
        assert kpi.total_products == 100
        assert kpi.deals_today == 5
        assert kpi.avg_discount_pct == 15.5
