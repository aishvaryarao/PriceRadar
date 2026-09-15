"""Data pipeline for cleaning, deduplication, and loading."""
from src.pipeline.cleaner import (
    clean_price,
    clean_discount,
    clean_rating,
    clean_product,
    deduplicate,
)
from src.pipeline.loader import get_connection, upsert_product, insert_price, load_batch
from src.pipeline.scheduler import scrape_and_load

__all__ = [
    "clean_price",
    "clean_discount",
    "clean_rating",
    "clean_product",
    "deduplicate",
    "get_connection",
    "upsert_product",
    "insert_price",
    "load_batch",
    "scrape_and_load",
]
