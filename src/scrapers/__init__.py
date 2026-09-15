"""Web scraping modules for price collection."""
from src.scrapers.base import BaseScraper
from src.scrapers.amazon import AmazonScraper
from src.scrapers.flipkart import FlipkartScraper

__all__ = ["BaseScraper", "AmazonScraper", "FlipkartScraper"]
