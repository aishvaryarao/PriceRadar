"""Scheduled pipeline for scraping and loading data."""

import asyncio
import logging
import os

from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Load environment variables from .env file
load_dotenv()

from src.scrapers.amazon import AmazonScraper
from src.scrapers.flipkart import FlipkartScraper
from src.pipeline.cleaner import clean_product, deduplicate
from src.pipeline.loader import (
    load_batch,
    get_db_context,
    refresh_price_summary,
)

logger = logging.getLogger(__name__)


# TEST MODE:
# We are testing one category first.
SCRAPE_CATEGORIES = [
    "smartphones",
    "laptops",
    "headphones",
    "face wash",
    "protein powder",
    "running shoes",
    "books",
    "smart watch",
    "bluetooth speaker",
    "gaming mouse",
]

SCRAPE_INTERVAL_HOURS: int = int(
    os.getenv("SCRAPE_INTERVAL_HOURS", "6")
)


async def scrape_and_load() -> dict[str, int]:
    """Run complete scraping and loading pipeline.

    Scrapes configured categories from Amazon and Flipkart,
    cleans data, removes duplicates, and loads to database.

    Returns:
        Statistics dictionary with counts.
    """

    logger.info("Starting scraping pipeline")

    stats = {
        "total_scraped": 0,
        "new_products": 0,
        "deals_found": 0,
        "errors": 0,
    }

    all_products = []

    # Initialize scrapers
    amazon_scraper = AmazonScraper()
    flipkart_scraper = FlipkartScraper()

    try:

        # ---------------------------------------------------------
        # SCRAPING
        # ---------------------------------------------------------

        for category in SCRAPE_CATEGORIES:

            logger.info(f"Scraping category: {category}")

            # -------------------------
            # Amazon
            # -------------------------

            try:

                amazon_products = await amazon_scraper.search(
                    category,
                    pages=2,
                )

                logger.info(
                    f"Amazon found {len(amazon_products)} "
                    f"products for {category}"
                )

                all_products.extend(amazon_products)

            except Exception as e:

                logger.error(
                    f"Amazon scrape failed for {category}: {e}"
                )

                stats["errors"] += 1

            # -------------------------
            # Flipkart
            # -------------------------

            try:

                flipkart_products = await flipkart_scraper.search(
                    category,
                    pages=2,
                )

                logger.info(
                    f"Flipkart found {len(flipkart_products)} "
                    f"products for {category}"
                )

                all_products.extend(flipkart_products)

            except Exception as e:

                logger.error(
                    f"Flipkart scrape failed for {category}: {e}"
                )

                stats["errors"] += 1

        # ---------------------------------------------------------
        # SCRAPING SUMMARY
        # ---------------------------------------------------------

        logger.info(
            f"Total products scraped: {len(all_products)}"
        )

        stats["total_scraped"] = len(all_products)

        # ---------------------------------------------------------
        # CLEAN DATA
        # ---------------------------------------------------------

        cleaned_products = [
            clean_product(product)
            for product in all_products
        ]

        cleaned_products = [
            product
            for product in cleaned_products
            if product is not None
        ]

        logger.info(
            f"After cleaning: {len(cleaned_products)} products"
        )

        # ---------------------------------------------------------
        # DEDUPLICATE
        # ---------------------------------------------------------

        deduplicated = deduplicate(cleaned_products)

        logger.info(
            f"After deduplication: {len(deduplicated)} products"
        )

        # ---------------------------------------------------------
        # LOAD INTO DATABASE
        # ---------------------------------------------------------

        load_result = load_batch(deduplicated)

        stats["new_products"] = load_result.get(
            "inserted",
            0,
        )

        logger.info(
            f"Database load result: {load_result}"
        )

        # ---------------------------------------------------------
        # REFRESH MATERIALIZED VIEW
        # ---------------------------------------------------------

        try:

            with get_db_context() as conn:

                refresh_price_summary(conn)

            logger.info(
                "price_summary refreshed successfully"
            )

        except Exception as e:

            logger.error(
                f"Failed to refresh price summary: {e}"
            )

            stats["errors"] += 1

        # ---------------------------------------------------------
        # COMPLETE
        # ---------------------------------------------------------

        logger.info(
            f"Pipeline complete: {stats}"
        )

    except Exception as e:

        logger.error(
            f"Pipeline failed: {e}"
        )

        stats["errors"] += 1

    finally:

        # ---------------------------------------------------------
        # CLOSE SCRAPERS
        # ---------------------------------------------------------

        try:

            await amazon_scraper.close()
            await flipkart_scraper.close()

            logger.info(
                "Scrapers closed successfully"
            )

        except Exception as e:

            logger.error(
                f"Error closing scrapers: {e}"
            )

            stats["errors"] += 1

    return stats


def run_scrape_sync() -> None:
    """Synchronous wrapper for async pipeline."""

    try:

        asyncio.run(
            scrape_and_load()
        )

    except Exception as e:

        logger.error(
            f"Scheduled scrape failed: {e}"
        )


class PipelineScheduler:
    """Manages scheduled scraping pipeline."""

    def __init__(self) -> None:
        """Initialize scheduler."""

        self.scheduler: BackgroundScheduler | None = None

    def start(
        self,
        run_immediately: bool = True,
    ) -> None:
        """Start the scheduler.

        Args:
            run_immediately:
                If True, run pipeline once on startup.
        """

        logger.info(
            f"Starting pipeline scheduler "
            f"({SCRAPE_INTERVAL_HOURS}h interval)"
        )

        self.scheduler = BackgroundScheduler()

        self.scheduler.add_job(
            run_scrape_sync,
            trigger=IntervalTrigger(
                hours=SCRAPE_INTERVAL_HOURS
            ),
            id="scrape_pipeline",
            name="Scrape all categories",
            replace_existing=True,
        )

        self.scheduler.start()

        logger.info(
            "Scheduler started successfully"
        )

        # Run once immediately for testing
        if run_immediately:

            logger.info(
                "Running initial pipeline"
            )

            run_scrape_sync()

    def stop(self) -> None:
        """Stop the scheduler."""

        if self.scheduler:

            self.scheduler.shutdown(
                wait=False
            )

            logger.info(
                "Scheduler stopped"
            )

    def get_job(self):
        """Get the scrape job."""

        if self.scheduler:

            return self.scheduler.get_job(
                "scrape_pipeline"
            )

        return None