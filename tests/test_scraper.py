"""Tests for scraper and data cleaning."""
import pytest
from src.pipeline.cleaner import (
    clean_price,
    clean_discount,
    clean_rating,
    clean_product,
    deduplicate,
)
from src.models.deal_detector import DealDetector


class TestCleaner:
    """Tests for data cleaning functions."""

    def test_clean_price_with_currency_symbol(self):
        """Test cleaning price with ₹ symbol."""
        assert clean_price("₹1,299") == 1299

    def test_clean_price_with_decimal(self):
        """Test cleaning price with decimal."""
        assert clean_price("1299.50") == 1299

    def test_clean_price_with_commas(self):
        """Test cleaning price with commas."""
        assert clean_price("1,299") == 1299

    def test_clean_price_empty(self):
        """Test cleaning empty price."""
        assert clean_price(None) is None
        assert clean_price("") is None

    def test_clean_discount_with_percent(self):
        """Test cleaning discount with % symbol."""
        assert clean_discount("23% off") == 23.0

    def test_clean_discount_with_off(self):
        """Test cleaning discount with 'off' text."""
        assert clean_discount("23% off") == 23.0

    def test_clean_discount_number_only(self):
        """Test cleaning discount as number."""
        assert clean_discount("23") == 23.0

    def test_clean_discount_empty(self):
        """Test cleaning empty discount."""
        assert clean_discount(None) is None

    def test_clean_rating_valid(self):
        """Test cleaning valid rating."""
        assert clean_rating("4.2 out of 5") == 4.2

    def test_clean_rating_number_only(self):
        """Test cleaning rating as number."""
        assert clean_rating("4.2") == 4.2

    def test_clean_rating_invalid(self):
        """Test cleaning invalid rating."""
        assert clean_rating("6.0") is None  # > 5
        assert clean_rating("-1") is None  # < 0

    def test_clean_rating_empty(self):
        """Test cleaning empty rating."""
        assert clean_rating(None) is None

    def test_clean_product_valid(self):
        """Test cleaning valid product."""
        raw = {
            "name": "iPhone 15",
            "price": "₹79,999",
            "brand": "Apple",
            "platform": "amazon",
        }
        result = clean_product(raw)
        assert result is not None
        assert result["name"] == "iPhone 15"
        assert result["price"] == 79999

    def test_clean_product_missing_name(self):
        """Test cleaning product without name."""
        raw = {"price": "₹1,000", "platform": "amazon"}
        result = clean_product(raw)
        assert result is None

    def test_clean_product_missing_price(self):
        """Test cleaning product without price."""
        raw = {"name": "Product", "platform": "amazon"}
        result = clean_product(raw)
        assert result is None

    def test_deduplicate_removes_similar(self):
        """Test deduplication removes similar names."""
        products = [
            {"name": "iPhone 15 Pro", "price": 100000},
            {"name": "iPhone 15 Pro Max", "price": 120000},
            {"name": "iPhone 15 Pro", "price": 95000},  # Duplicate, lower price
        ]
        result = deduplicate(products)
        assert len(result) == 2
        # Lower price should be kept
        iphone_pro = [p for p in result if "15 Pro" in p["name"] and "Max" not in p["name"]][0]
        assert iphone_pro["price"] == 95000

    def test_deduplicate_empty_list(self):
        """Test deduplication with empty list."""
        assert deduplicate([]) == []


class TestDealDetector:
    """Tests for ML deal detector."""

    def test_detector_init(self):
        """Test detector initialization."""
        detector = DealDetector()
        assert detector.is_trained is False
        assert detector.model is None

    def test_detector_train(self):
        """Test detector training."""
        detector = DealDetector()
        accuracy = detector.train()
        assert 0 <= accuracy <= 1
        assert detector.is_trained is True
        assert detector.model is not None

    def test_detector_predict_untrained(self):
        """Test prediction with untrained model."""
        detector = DealDetector()
        result = detector.predict(
            {
                "drop_from_max_pct": 30,
                "price_vs_avg7d": 0.9,
                "price_vs_avg30d": 0.85,
                "price_volatility": 0.2,
            }
        )
        assert result["label"] == "NORMAL"
        assert result["confidence"] == 0.0

    def test_detector_predict_trained(self):
        """Test prediction with trained model."""
        detector = DealDetector()
        detector.train()

        result = detector.predict(
            {
                "drop_from_max_pct": 30,
                "price_vs_avg7d": 0.9,
                "price_vs_avg30d": 0.85,
                "price_volatility": 0.2,
            }
        )

        assert "label" in result
        assert "confidence" in result
        assert "reason" in result
        assert 0 <= result["confidence"] <= 1
