"""Abstract base class for web scrapers."""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any
from pathlib import Path

from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for e-commerce scrapers."""

    USER_AGENTS: list[str] = [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
            "Gecko/20100101 Firefox/121.0"
        ),
    ]

    def __init__(self) -> None:
        """Initialize scraper with user agent."""
        self.ua = UserAgent()
        self.session = None
        self.browser = None
        self.context = None

    def get_random_ua(self) -> str:
        """Get a random user agent string.

        Returns:
            str: Random user agent from predefined list.
        """
        import random

        return random.choice(self.USER_AGENTS)

    async def random_delay(self) -> None:
        """Sleep for random duration between 2-5 seconds.

        This prevents detection as a bot.
        """
        import random

        delay: float = random.uniform(2, 5)
        await asyncio.sleep(delay)
        logger.debug(f"Applied {delay:.2f}s random delay")

    @abstractmethod
    async def search(self, query: str, pages: int = 2) -> list[dict[str, Any]]:
        """Search for products on the platform.

        Args:
            query: Search keyword
            pages: Number of result pages to scrape

        Returns:
            List of product dictionaries
        """
        pass

    @abstractmethod
    async def scrape_product(self, url: str) -> dict[str, Any] | None:
        """Get detailed product information from a URL.

        Args:
            url: Product page URL

        Returns:
            Product details dict or None if failed
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close browser and session resources."""
        pass
