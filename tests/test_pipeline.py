"""Tests for data pipeline."""
import pytest
from src.pipeline.cleaner import clean_product, deduplicate


class TestPipeline:
    """Tests for data pipeline."""

    def test_clean_product_complete(self):
        """Test complete product cleaning."""
        raw = {
            "name": " iPhone 15 Pro ",
            "brand": "Apple",
            "category": "Smartphones",
            "platform": " AMAZON ",
            "url": "https://amazon.in/dp/...",
            "price": "₹79,999.00",
            "original_price": "₹99,999",
            "discount_pct": "20% off",
            "rating": "4.5 out of 5",
            "review_count": "1234",
            "image_url": "https://example.com/image.jpg",
        }

        cleaned = clean_product(raw)

        assert cleaned is not None
        assert cleaned["name"] == "iPhone 15 Pro"
        assert cleaned["brand"] == "Apple"
        assert cleaned["platform"] == "amazon"
        assert cleaned["price"] == 79999
        assert cleaned["original_price"] == 99999
        assert cleaned["discount_pct"] == 20.0
        assert cleaned["rating"] == 4.5
        assert cleaned["review_count"] == 1234

    def test_batch_deduplication(self):
        """Test batch deduplication with multiple categories."""
        products = [
            {"name": "iPhone 15", "price": 79999, "category": "phones"},
            {"name": "iPhone 15 Pro", "price": 89999, "category": "phones"},
            {"name": "iPhone 15", "price": 75000, "category": "phones"},  # Dup
            {"name": "Samsung S24", "price": 79999, "category": "phones"},
            {"name": "MacBook Pro 14", "price": 199999, "category": "laptops"},
            {"name": "MacBook Pro 14", "price": 195000, "category": "laptops"},  # Dup
        ]

        deduplicated = deduplicate(products)

        # Should have removed 2 duplicates
        assert len(deduplicated) == 4

        # iPhone 15 should have lower price
        iphone = [p for p in deduplicated if p["name"] == "iPhone 15"][0]
        assert iphone["price"] == 75000
