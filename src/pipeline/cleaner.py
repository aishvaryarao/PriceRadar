"""Data cleaning and preprocessing utilities."""
import logging
import re
from typing import Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def clean_price(raw: str | None) -> int | None:
    """Clean and convert price string to integer.

    Handles various formats: '₹1,299', '1299.00', '1,299', None, ''

    Args:
        raw: Raw price string

    Returns:
        Integer price or None if invalid
    """
    if not raw or not isinstance(raw, str):
        return None

    try:
        # Remove currency symbols and whitespace
        cleaned = raw.replace("₹", "").replace("$", "").strip()

        # Remove commas
        cleaned = cleaned.replace(",", "")

        # Convert to float then int
        price_float = float(cleaned)
        return int(price_float)

    except (ValueError, AttributeError, TypeError):
        logger.debug(f"Could not clean price: {raw}")
        return None


def clean_discount(raw: str | None) -> float | None:
    """Clean and convert discount string to percentage float.

    Handles: '23% off', '23%', '23', None

    Args:
        raw: Raw discount string

    Returns:
        Float discount percentage or None
    """
    if not raw or not isinstance(raw, str):
        return None

    try:
        # Remove % symbol and 'off' text
        cleaned = raw.replace("%", "").replace("off", "").strip()

        # Extract number
        match = re.search(r"[\d.]+", cleaned)
        if match:
            return float(match.group())

        return None

    except (ValueError, AttributeError, TypeError):
        logger.debug(f"Could not clean discount: {raw}")
        return None


def clean_rating(raw: str | None) -> float | None:
    """Clean and convert rating string to float.

    Handles: '4.2 out of 5', '4.2', None

    Args:
        raw: Raw rating string

    Returns:
        Float rating (0-5) or None
    """
    if not raw or not isinstance(raw, str):
        return None

    try:
        # Extract first decimal number
        match = re.search(r"[\d.]+", raw)
        if match:
            rating = float(match.group())
            # Validate rating is between 0 and 5
            if 0 <= rating <= 5:
                return rating

        return None

    except (ValueError, AttributeError, TypeError):
        logger.debug(f"Could not clean rating: {raw}")
        return None


def clean_product(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Clean all fields in a product dictionary.

    Args:
        raw: Raw product data

    Returns:
        Cleaned product dict or None if critical fields missing
    """
    if not raw or not isinstance(raw, dict):
        return None

    try:
        cleaned = {
            "name": raw.get("name", "").strip() if raw.get("name") else None,
            "brand": raw.get("brand", "").strip() if raw.get("brand") else None,
            "category": raw.get("category", "").strip() if raw.get("category") else None,
            "platform": raw.get("platform", "").lower() if raw.get("platform") else None,
            "url": raw.get("url", "").strip() if raw.get("url") else None,
            "image_url": raw.get("image_url", "").strip() if raw.get("image_url") else None,
            "product_id_on_platform": (
                str(raw.get("product_id_on_platform", "")).strip()
                if raw.get("product_id_on_platform")
                else None
            ),
            "price": clean_price(raw.get("price")),
            "original_price": clean_price(raw.get("original_price")),
            "discount_pct": clean_discount(raw.get("discount_pct")),
            "rating": clean_rating(raw.get("rating")),
            "review_count": (
                int(raw.get("review_count"))
                if raw.get("review_count") and isinstance(raw.get("review_count"), (int, str))
                and str(raw.get("review_count")).isdigit()
                else None
            ),
        }

        # Validate critical fields
        if not cleaned.get("name") or not cleaned.get("price"):
            logger.debug(f"Product missing critical fields: {cleaned}")
            return None

        return cleaned

    except Exception as e:
        logger.warning(f"Error cleaning product: {e}")
        return None


def deduplicate(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate products by name similarity.

    Keep the product with lower price when duplicates found.

    Args:
        products: List of product dictionaries

    Returns:
        Deduplicated list of products
    """
    if not products:
        return []

    seen: dict[str, dict[str, Any]] = {}
    threshold: float = 0.85

    for product in products:
        name = product.get("name", "").lower()

        if not name:
            continue

        # Check against existing products
        found_duplicate = False

        for seen_name, seen_product in seen.items():
            # Calculate similarity ratio
            similarity = SequenceMatcher(None, name, seen_name).ratio()

            if similarity > threshold:
                # Keep product with lower price
                current_price = product.get("price", float("inf"))
                seen_price = seen_product.get("price", float("inf"))

                if current_price < seen_price:
                    seen[seen_name] = product
                    logger.debug(f"Duplicate found: {name}, keeping lower price")

                found_duplicate = True
                break

        if not found_duplicate:
            seen[name] = product

    result = list(seen.values())
    logger.info(f"Deduplicated {len(products)} -> {len(result)} products")
    return result
