"""Analytics and reporting queries."""

import logging
from typing import Any

import pandas as pd

from src.pipeline.loader import get_db_context

logger = logging.getLogger(__name__)


def get_top_deals(
    limit: int = 20,
    category: str | None = None,
) -> pd.DataFrame:
    """Get products with price features for deal detection."""

    try:
        with get_db_context() as conn:
            query = """
                WITH latest_prices AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        price AS current_price
                    FROM price_history
                    WHERE scraped_at >= NOW() - INTERVAL '30 days'
                    ORDER BY product_id, scraped_at DESC
                ),

                price_stats AS (
                    SELECT
                        product_id,

                        MAX(price) AS max_30d,

                        MIN(price) AS min_30d,

                        AVG(price) FILTER (
                            WHERE scraped_at >= NOW() - INTERVAL '7 days'
                        ) AS avg_7d,

                        AVG(price) FILTER (
                            WHERE scraped_at >= NOW() - INTERVAL '30 days'
                        ) AS avg_30d,

                        (
                            STDDEV_POP(price) FILTER (
                                WHERE scraped_at >= NOW() - INTERVAL '30 days'
                            )
                            /
                            NULLIF(
                                AVG(price) FILTER (
                                    WHERE scraped_at >= NOW() - INTERVAL '30 days'
                                ),
                                0
                            )
                        ) AS price_volatility

                    FROM price_history

                    WHERE scraped_at >= NOW() - INTERVAL '30 days'

                    GROUP BY product_id
                )

                SELECT
                    p.id,
                    p.name,
                    p.platform,

                    lp.current_price,

                    ps.min_30d,
                    ps.max_30d,
                    ps.avg_7d,
                    ps.avg_30d,

                    COALESCE(
                        ps.price_volatility,
                        0
                    ) AS price_volatility,

                    COALESCE(
                        p.rating,
                        0
                    ) AS rating,

                    p.category,
                    p.url,
                    p.image_url

                FROM products p

                JOIN latest_prices lp
                    ON p.id = lp.product_id

                JOIN price_stats ps
                    ON p.id = ps.product_id

                WHERE (
                    %s IS NULL
                    OR p.category = %s
                )

                ORDER BY
                    CASE
                        WHEN ps.max_30d > 0
                        THEN (
                            (ps.max_30d - lp.current_price)
                            * 100.0
                            / ps.max_30d
                        )
                        ELSE 0
                    END DESC

                LIMIT %s
            """

            df = pd.read_sql_query(
                query,
                conn,
                params=(
                    category,
                    category,
                    limit,
                ),
            )

            if df.empty:
                return pd.DataFrame()

            # Handle missing optional values.
            df = df.fillna(
                {
                    "image_url": "",
                    "url": "",
                    "category": "",
                    "price_volatility": 0,
                    "avg_7d": 0,
                    "avg_30d": 0,
                }
            )

            # --------------------------------------------------
            # Feature 1: Drop from 30-day maximum
            # --------------------------------------------------

            df["drop_from_max_pct"] = (
                (
                    df["max_30d"]
                    - df["current_price"]
                )
                * 100.0
                / df["max_30d"].replace(
                    0,
                    pd.NA,
                )
            ).fillna(0).round(2)

            # --------------------------------------------------
            # Feature 2: Current price vs 7-day average
            # --------------------------------------------------

            df["price_vs_avg7d"] = (
                df["current_price"]
                / df["avg_7d"].replace(
                    0,
                    pd.NA,
                )
            ).fillna(1.0).round(4)

            # --------------------------------------------------
            # Feature 3: Current price vs 30-day average
            # --------------------------------------------------

            df["price_vs_avg30d"] = (
                df["current_price"]
                / df["avg_30d"].replace(
                    0,
                    pd.NA,
                )
            ).fillna(1.0).round(4)

            # --------------------------------------------------
            # Feature 4:
            # Normalized price volatility
            # --------------------------------------------------

            df["price_volatility"] = (
                df["price_volatility"]
                .fillna(0)
                .round(4)
            )

            logger.info(
                "Retrieved %s products with deal features",
                len(df),
            )

            return df

    except Exception as e:
        logger.error(
            "Error getting top deals: %s",
            e,
        )

        return pd.DataFrame()


def get_price_history(
    product_id: int,
    days: int = 30,
) -> pd.DataFrame:
    """Get price history for a product."""

    try:
        with get_db_context() as conn:
            query = """
                SELECT
                    scraped_at,
                    price
                FROM price_history
                WHERE product_id = %s
                  AND scraped_at >= NOW()
                      - (%s * INTERVAL '1 day')
                ORDER BY scraped_at ASC
            """

            df = pd.read_sql_query(
                query,
                conn,
                params=(
                    product_id,
                    days,
                ),
            )

            logger.info(
                "Retrieved %s price history records "
                "for product %s",
                len(df),
                product_id,
            )

            return df

    except Exception as e:
        logger.error(
            "Error getting price history: %s",
            e,
        )

        return pd.DataFrame()


def get_platform_comparison(
    name: str,
) -> pd.DataFrame:
    """Compare product prices across platforms."""

    try:
        with get_db_context() as conn:
            query = """
                WITH latest_prices AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        price AS current_price
                    FROM price_history
                    ORDER BY product_id, scraped_at DESC
                ),

                price_stats AS (
                    SELECT
                        product_id,
                        AVG(price) AS avg_30d,
                        MAX(price) AS max_30d
                    FROM price_history
                    WHERE scraped_at >= NOW()
                        - INTERVAL '30 days'
                    GROUP BY product_id
                )

                SELECT
                    p.platform,
                    p.name,
                    lp.current_price,
                    ps.avg_30d,

                    CASE
                        WHEN ps.max_30d > 0
                        THEN ROUND(
                            (
                                (
                                    ps.max_30d
                                    - lp.current_price
                                )
                                * 100.0
                                / ps.max_30d
                            )::numeric,
                            2
                        )
                        ELSE 0
                    END AS drop_from_max_pct,

                    p.url

                FROM products p

                JOIN latest_prices lp
                    ON p.id = lp.product_id

                JOIN price_stats ps
                    ON p.id = ps.product_id

                WHERE p.name ILIKE %s

                ORDER BY
                    p.platform,
                    lp.current_price
            """

            df = pd.read_sql_query(
                query,
                conn,
                params=(f"%{name}%",),
            )

            logger.info(
                "Retrieved platform comparison for %s",
                name,
            )

            return df

    except Exception as e:
        logger.error(
            "Error getting platform comparison: %s",
            e,
        )

        return pd.DataFrame()


def get_category_trends() -> pd.DataFrame:
    """Get average price trends by category over the last 30 days."""

    try:
        with get_db_context() as conn:
            query = """
                WITH latest_prices AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        price AS current_price
                    FROM price_history
                    ORDER BY product_id, scraped_at DESC
                ),

                price_stats AS (
                    SELECT
                        product_id,
                        AVG(price) AS avg_30d,
                        MAX(price) AS max_30d
                    FROM price_history
                    WHERE scraped_at >= NOW()
                        - INTERVAL '30 days'
                    GROUP BY product_id
                )

                SELECT
                    p.category,

                    COUNT(DISTINCT p.id)
                        AS product_count,

                    ROUND(
                        AVG(lp.current_price),
                        2
                    ) AS avg_current_price,

                    ROUND(
                        AVG(ps.avg_30d),
                        2
                    ) AS avg_30d,

                    ROUND(
                        PERCENTILE_CONT(0.5)
                        WITHIN GROUP (
                            ORDER BY
                                CASE
                                    WHEN ps.max_30d > 0
                                    THEN (
                                        ps.max_30d
                                        - lp.current_price
                                    )
                                    * 100.0
                                    / ps.max_30d
                                    ELSE 0
                                END
                        )::numeric,
                        2
                    ) AS median_drop_pct

                FROM products p

                JOIN latest_prices lp
                    ON p.id = lp.product_id

                JOIN price_stats ps
                    ON p.id = ps.product_id

                WHERE p.category IS NOT NULL

                GROUP BY p.category

                ORDER BY avg_current_price DESC
            """

            df = pd.read_sql_query(
                query,
                conn,
            )

            logger.info(
                "Retrieved trends for %s categories",
                len(df),
            )

            return df

    except Exception as e:
        logger.error(
            "Error getting category trends: %s",
            e,
        )

        return pd.DataFrame()


def get_kpi_summary() -> dict[str, Any]:
    """Get key performance indicators summary."""

    try:
        with get_db_context() as conn:
            cursor = conn.cursor()

            # --------------------------------------------------
            # Total products
            # --------------------------------------------------

            cursor.execute(
                "SELECT COUNT(*) FROM products"
            )

            result = cursor.fetchone()

            total_products = (
                result[0]
                if result
                else 0
            )

            # --------------------------------------------------
            # Deals today
            # --------------------------------------------------

            cursor.execute(
                """
                WITH latest_prices AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        price AS current_price
                    FROM price_history
                    ORDER BY product_id, scraped_at DESC
                ),

                max_prices AS (
                    SELECT
                        product_id,
                        MAX(price) AS max_price
                    FROM price_history
                    GROUP BY product_id
                )

                SELECT COUNT(*)

                FROM latest_prices lp

                JOIN max_prices mp
                    ON lp.product_id = mp.product_id

                WHERE mp.max_price > 0

                  AND lp.current_price
                      <= mp.max_price * 0.95
                """
            )

            result = cursor.fetchone()

            deals_today = (
                result[0]
                if result
                else 0
            )

            # --------------------------------------------------
            # Average discount
            # --------------------------------------------------

            cursor.execute(
                """
                WITH latest_prices AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        price AS current_price
                    FROM price_history
                    ORDER BY product_id, scraped_at DESC
                ),

                max_prices AS (
                    SELECT
                        product_id,
                        MAX(price) AS max_price
                    FROM price_history
                    GROUP BY product_id
                )

                SELECT AVG(
                    CASE
                        WHEN mp.max_price > 0
                        THEN (
                            mp.max_price
                            - lp.current_price
                        )
                        * 100.0
                        / mp.max_price

                        ELSE 0
                    END
                )

                FROM latest_prices lp

                JOIN max_prices mp
                    ON lp.product_id = mp.product_id
                """
            )

            result = cursor.fetchone()

            avg_discount_pct = (
                result[0]
                if result
                and result[0] is not None
                else 0.0
            )

            # --------------------------------------------------
            # Best current deal
            # --------------------------------------------------

            cursor.execute(
                """
                WITH latest_prices AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        price AS current_price
                    FROM price_history
                    ORDER BY product_id, scraped_at DESC
                ),

                max_prices AS (
                    SELECT
                        product_id,
                        MAX(price) AS max_price
                    FROM price_history
                    GROUP BY product_id
                )

                SELECT
                    p.name,
                    (
                        mp.max_price
                        - lp.current_price
                    ) AS saving

                FROM products p

                JOIN latest_prices lp
                    ON p.id = lp.product_id

                JOIN max_prices mp
                    ON p.id = mp.product_id

                ORDER BY
                    CASE
                        WHEN mp.max_price > 0
                        THEN (
                            mp.max_price
                            - lp.current_price
                        )
                        * 100.0
                        / mp.max_price

                        ELSE 0
                    END DESC

                LIMIT 1
                """
            )

            best_deal = cursor.fetchone()

            best_deal_name = (
                best_deal[0]
                if best_deal
                else None
            )

            best_deal_saving = (
                float(best_deal[1])
                if best_deal
                else 0
            )

            # --------------------------------------------------
            # Most recent scrape
            # --------------------------------------------------

            cursor.execute(
                "SELECT MAX(scraped_at) "
                "FROM price_history"
            )

            result = cursor.fetchone()

            last_scraped = (
                result[0]
                if result
                else None
            )

            cursor.close()

            if last_scraped:

                last_scraped_str = (
                    last_scraped
                    if isinstance(
                        last_scraped,
                        str,
                    )
                    else last_scraped.isoformat()
                )

            else:

                last_scraped_str = None

            return {
                "total_products": total_products,
                "deals_today": deals_today,
                "avg_discount_pct": round(
                    float(avg_discount_pct),
                    2,
                ),
                "best_deal_name": best_deal_name,
                "best_deal_saving": best_deal_saving,
                "last_scraped_at": last_scraped_str,
            }

    except Exception as e:

        logger.error(
            "Error getting KPI summary: %s",
            e,
        )

        return {
            "total_products": 0,
            "deals_today": 0,
            "avg_discount_pct": 0.0,
            "best_deal_name": None,
            "best_deal_saving": 0,
            "last_scraped_at": None,
        }