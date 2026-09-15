"""Flipkart India web scraper using Playwright."""
import logging
from typing import Any

from playwright.async_api import async_playwright, Browser, BrowserContext
from src.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)
FLIPKART_BASE_URL: str = "https://www.flipkart.com"


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart marketplace."""

    def __init__(self) -> None:
        """Initialize Flipkart scraper."""
        super().__init__()
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.base_url: str = FLIPKART_BASE_URL

    async def _init_browser(self) -> None:
        """Initialize Playwright browser with anti-detection."""
        if self.browser is None:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent=self.get_random_ua(),
                viewport={"width": 1920, "height": 1080},
                locale="en-IN",
            )
            logger.info("Browser initialized for Flipkart scraping")

    async def search(self, query: str, pages: int = 2) -> list[dict[str, Any]]:
        """Search for products on Flipkart.

        Args:
            query: Search keywords
            pages: Number of pages to scrape

        Returns:
            List of product data dictionaries
        """
        await self._init_browser()
        products: list[dict[str, Any]] = []

        try:
            for page_num in range(1, pages + 1):
                logger.info(f"Scraping Flipkart search: {query}, page {page_num}")
                url = f"{self.base_url}/search?q={query}&page={page_num}"

                page = await self.context.new_page()
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Anti-detection: hide webdriver
                await page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', {get: () => false}); }")

                # Close login popup if present
                try:
                    close_btn = await page.query_selector("span._2KpZ6l")
                    if close_btn:
                        await close_btn.click(timeout=5000)
                except Exception as e:
                    logger.debug(f"Popup close failed (expected): {e}")

                # Wait for product cards (try multiple selectors for resilience)
                product_cards = []
                selectors = [
                    "div._1AtVbE",  # Original Flipkart selector
                    "[data-test-id='productCardImg']",  # Alternative data-test-id
                    "div.productCard",  # Generic product card class
                    "a._1fGeJ5",  # Product link selector
                    "div[class*='productCard']",  # Product card with any class variant
                ]
                
                for selector in selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        product_cards = await page.query_selector_all(selector)
                        if product_cards:
                            logger.info(f"Found {len(product_cards)} products using selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not product_cards:
                    logger.warning(f"Product cards not found on page {page_num}")
                    await page.close()
                    continue

                # Extract product data

                for card in product_cards:
                    try:
                        product_data = await self._extract_product_data(card)
                        if product_data:
                            product_data["platform"] = "flipkart"
                            products.append(product_data)

                    except Exception as e:
                        logger.warning(f"Error extracting product card: {e}")
                        continue

                await page.close()
                await self.random_delay()

            logger.info(f"Flipkart search complete: {query} - {len(products)} products found")
            return products

        except Exception as e:
            logger.error(f"Error during Flipkart search: {e}")
            return products

    async def _extract_product_data(self, card: Any) -> dict[str, Any] | None:
        """Extract product information from a card element.

        Args:
            card: Playwright element selector

        Returns:
            Dictionary with product data or None
        """
        try:
            # Product name
            name_elem = await card.query_selector("a.s1Q50cHSZFz7PK3IUxTBm")
            name = await name_elem.text_content() if name_elem else None

            if not name:
                return None

            # Price
            price_elem = await card.query_selector("div._30jeq3")
            price_text = await price_elem.text_content() if price_elem else None
            price = self._clean_price_str(price_text) if price_text else None

            if not price:
                return None

            # Original price
            original_price_elem = await card.query_selector("div._3I9_wc")
            original_price_text = await original_price_elem.text_content() if original_price_elem else None
            original_price = self._clean_price_str(original_price_text) if original_price_text else None

            # Discount percentage
            discount_elem = await card.query_selector("div._3Ay6Sb")
            discount_text = await discount_elem.text_content() if discount_elem else None
            discount_pct = self._clean_discount_str(discount_text) if discount_text else None

            # Image URL
            img_elem = await card.query_selector("img.DByuf4")
            image_url = await img_elem.get_attribute("src") if img_elem else None

            # Product URL
            link_elem = await card.query_selector("a.s1Q50cHSZFz7PK3IUxTBm")
            product_url = await link_elem.get_attribute("href") if link_elem else None
            if product_url and not product_url.startswith("http"):
                product_url = f"{self.base_url}{product_url}"

            # Product ID (pid parameter)
            pid = None
            if product_url and "pid=" in product_url:
                try:
                    pid = product_url.split("pid=")[1].split("&")[0]
                except IndexError:
                    pass

            # Rating
            rating_elem = await card.query_selector("div._1kYiGH")
            rating_text = await rating_elem.text_content() if rating_elem else None
            rating = self._clean_rating_str(rating_text) if rating_text else None

            # Review count
            review_elem = await card.query_selector("span._2_R_DZ")
            review_text = await review_elem.text_content() if review_elem else None
            review_count = None
            if review_text:
                try:
                    review_count = int(review_text.replace(",", ""))
                except (ValueError, AttributeError):
                    pass

            return {
                "name": name.strip(),
                "brand": None,
                "category": None,
                "url": product_url,
                "image_url": image_url,
                "product_id_on_platform": pid,
                "price": price,
                "original_price": original_price,
                "discount_pct": discount_pct,
                "rating": rating,
                "review_count": review_count,
            }

        except Exception as e:
            logger.warning(f"Error extracting product data: {e}")
            return None

    async def scrape_product(self, url: str) -> dict[str, Any] | None:
        """Get detailed product information from Flipkart product page.

        Args:
            url: Product page URL

        Returns:
            Product details or None
        """
        await self._init_browser()

        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Hide webdriver
            await page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', {get: () => false}); }")

            # Extract detailed information
            title_elem = await page.query_selector("span.VU-ZEz")
            title = await title_elem.text_content() if title_elem else None

            if not title:
                await page.close()
                return None

            price_elem = await page.query_selector("div._30jeq3")
            price_text = await price_elem.text_content() if price_elem else None
            price = self._clean_price_str(price_text) if price_text else None

            # Get rating
            rating_elem = await page.query_selector("div._1kYiGH")
            rating_text = await rating_elem.text_content() if rating_elem else None
            rating = self._clean_rating_str(rating_text) if rating_text else None

            # Get image
            img_elem = await page.query_selector("img.q6DClP")
            image_url = await img_elem.get_attribute("src") if img_elem else None

            await page.close()

            return {
                "name": title.strip(),
                "price": price,
                "rating": rating,
                "image_url": image_url,
                "url": url,
                "platform": "flipkart",
            }

        except Exception as e:
            logger.error(f"Error scraping product detail: {e}")
            return None

    @staticmethod
    def _clean_price_str(price_str: str | None) -> int | None:
        """Convert price string to integer.

        Args:
            price_str: Price string (e.g., '₹1,299')

        Returns:
            Integer price or None
        """
        if not price_str:
            return None

        try:
            cleaned = price_str.replace("₹", "").replace(",", "").strip()
            return int(float(cleaned))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _clean_discount_str(discount_str: str | None) -> float | None:
        """Convert discount string to float percentage.

        Args:
            discount_str: Discount string (e.g., '23% off')

        Returns:
            Float discount percentage or None
        """
        if not discount_str:
            return None

        try:
            cleaned = discount_str.replace("%", "").replace("off", "").strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _clean_rating_str(rating_str: str | None) -> float | None:
        """Convert rating string to float.

        Args:
            rating_str: Rating string (e.g., '4.2')

        Returns:
            Float rating or None
        """
        if not rating_str:
            return None

        try:
            rating_num = rating_str.split()[0]
            return float(rating_num)
        except (ValueError, IndexError, AttributeError):
            return None

    async def close(self) -> None:
        """Close browser and playwright resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Flipkart scraper closed")
        except Exception as e:
            logger.error(f"Error closing scraper: {e}")
