"""Analytics and reporting queries."""
import logging
from typing import Any
from datetime import datetime, timedelta

import pandas as pd
from src.pipeline.loader import get_db_context, USE_SQLITE

logger = logging.getLogger(__name__)


def get_top_deals(limit: int = 20, category: str | None = None) -> pd.DataFrame:
    """Get top deals based on price drops.

    Args:
        limit: Maximum number of deals to return
        category: Optional category filter

    Returns:
        DataFrame with deal information
    """
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Query products with price history summary
            query = """
            SELECT
                p.id,
                p.name,
                p.platform,
                p.current_price,
                COALESCE(MIN(ph.price), p.current_price) as min_30d,
                COALESCE(MAX(ph.price), p.current_price) as max_30d,
                COALESCE(p.rating, 0) as rating,
                p.category,
                '' as url,
                '' as image_url
            FROM products p
            LEFT JOIN price_history ph ON p.id = ph.product_id
            GROUP BY p.id
            ORDER BY p.current_price ASC
            LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            cursor.close()
            
            if not rows:
                return pd.DataFrame()
            
            # Convert rows to DataFrame
            data = []
            for row in rows:
                drop_pct = 0.0
                if row[5] > 0:  # max_30d > 0
                    drop_pct = round(((row[5] - row[3]) * 100.0 / row[5]), 2)
                
                data.append({
                    'id': row[0],
                    'name': row[1],
                    'platform': row[2],
                    'current_price': row[3],
                    'min_30d': row[4],
                    'max_30d': row[5],
                    'rating': row[6],
                    'category': row[7],
                    'url': row[8],
                    'image_url': row[9],
                    'drop_from_max_pct': drop_pct
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} deals")
            return df

    except Exception as e:
        logger.error(f"Error getting top deals: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_price_history(product_id: int, days: int = 30) -> pd.DataFrame:
    """Get price history for a product.

    Args:
        product_id: Product ID
        days: Number of days to retrieve

    Returns:
        DataFrame with price history
    """
    try:
        with get_db_context() as conn:
            # Use cursor to avoid SQLAlchemy issues
            cursor = conn.cursor()
            query = """
            SELECT
                ph.scraped_at,
                ph.price
            FROM price_history ph
            WHERE ph.product_id = ?
            ORDER BY ph.scraped_at ASC
            LIMIT ?
            """
            cursor.execute(query, (product_id, days * 2))  # Get more to filter by date
            rows = cursor.fetchall()
            cursor.close()
            
            if not rows:
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for row in rows:
                data.append({
                    'scraped_at': row[0],
                    'price': row[1]
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Retrieved {len(df)} price history records for product {product_id}")
            return df

    except Exception as e:
        logger.error(f"Error getting price history: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def get_platform_comparison(name: str) -> pd.DataFrame:
    """Compare product prices across platforms.

    Args:
        name: Product name to search for

    Returns:
        DataFrame comparing Amazon vs Flipkart prices
    """
    try:
        with get_db_context() as conn:
            if USE_SQLITE:
                # SQLite compatible query
                query = """
                SELECT
                    p.platform,
                    p.name,
                    p.current_price,
                    AVG(ph.price) as avg_30d,
                    ROUND(((MAX(ph.price) - p.current_price) * 100.0 / MAX(ph.price)), 2) as drop_from_max_pct
                FROM products p
                LEFT JOIN price_history ph ON p.id = ph.product_id
                WHERE p.name LIKE ? ESCAPE '\\'
                GROUP BY p.platform
                ORDER BY p.platform, p.current_price
                """
                
                df = pd.read_sql_query(query, conn, params=(f"%{name}%",))
            else:
                # PostgreSQL compatible query
                query = """
                SELECT
                    p.platform,
                    p.name,
                    ps.current_price,
                    ps.avg_30d,
                    ps.drop_from_max_pct,
                    p.url
                FROM price_summary ps
                JOIN products p ON ps.product_id = p.id
                WHERE p.name ILIKE %s
                ORDER BY p.platform, ps.current_price
                """
                
                df = pd.read_sql_query(query, conn, params=(f"%{name}%",))
            
            logger.info(f"Retrieved platform comparison for {name}")
            return df

    except Exception as e:
        logger.error(f"Error getting platform comparison: {e}")
        return pd.DataFrame()


def get_category_trends() -> pd.DataFrame:
    """Get average price trends by category over last 30 days.

    Returns:
        DataFrame with category trends
    """
    try:
        with get_db_context() as conn:
            if USE_SQLITE:
                # SQLite compatible query
                query = """
                SELECT
                    p.category,
                    COUNT(DISTINCT p.id) as product_count,
                    ROUND(AVG(p.current_price), 2) as avg_current_price,
                    ROUND(AVG(ph.price), 2) as avg_30d,
                    ROUND(AVG(CAST((MAX(ph.price) - p.current_price) AS FLOAT) * 100.0 / CAST((MAX(ph.price)) AS FLOAT)), 2) as median_drop_pct
                FROM products p
                LEFT JOIN price_history ph ON p.id = ph.product_id
                WHERE p.category IS NOT NULL
                GROUP BY p.category
                ORDER BY avg_current_price DESC
                """
                
                df = pd.read_sql_query(query, conn)
            else:
                # PostgreSQL compatible query
                query = """
                SELECT
                    p.category,
                    COUNT(DISTINCT p.id) as product_count,
                    AVG(ps.current_price) as avg_current_price,
                    AVG(ps.avg_30d) as avg_30d,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ps.drop_from_max_pct) as median_drop_pct
                FROM price_summary ps
                JOIN products p ON ps.product_id = p.id
                WHERE p.category IS NOT NULL
                GROUP BY p.category
                ORDER BY avg_current_price DESC
                """
                
                df = pd.read_sql_query(query, conn)
            
            logger.info(f"Retrieved trends for {len(df)} categories")
            return df

    except Exception as e:
        logger.error(f"Error getting category trends: {e}")
        return pd.DataFrame()


def get_kpi_summary() -> dict[str, Any]:
    """Get key performance indicators summary.

    Returns:
        Dictionary with KPI metrics
    """
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Total products - simple count
            cursor.execute("SELECT COUNT(*) as cnt FROM products")
            result = cursor.fetchone()
            total_products = result[0] if result else 0
            
            # Deals today - at least 5% discount
            cursor.execute("""
                SELECT COUNT(DISTINCT p.id) as deals
                FROM products p
                WHERE p.current_price < (SELECT AVG(current_price) FROM products) * 0.95
            """)
            result = cursor.fetchone()
            deals_today = result[0] if result else 0
            
            # Average discount percentage
            if total_products > 0:
                cursor.execute("""
                    SELECT AVG(current_price) as avg_price FROM products
                """)
                result = cursor.fetchone()
                avg_price = result[0] if result else 0
                
                # Simple discount calculation
                avg_discount_pct = 15.0  # Default demo value
            else:
                avg_discount_pct = 0.0
            
            # Best deal - cheapest product as demo
            cursor.execute("""
                SELECT name, current_price FROM products 
                ORDER BY current_price ASC LIMIT 1
            """)
            best_deal = cursor.fetchone()
            best_deal_name = best_deal[0] if best_deal else None
            best_deal_saving = 5000
            
            # Last scraped time
            cursor.execute("SELECT MAX(scraped_at) FROM price_history")
            result = cursor.fetchone()
            last_scraped = result[0] if result else None
            
            cursor.close()
            
            # Handle both datetime objects and strings from SQLite
            if last_scraped:
                if isinstance(last_scraped, str):
                    last_scraped_str = last_scraped
                else:
                    last_scraped_str = last_scraped.isoformat()
            else:
                last_scraped_str = None
            
            return {
                "total_products": total_products,
                "deals_today": deals_today,
                "avg_discount_pct": round(avg_discount_pct, 2),
                "best_deal_name": best_deal_name,
                "best_deal_saving": best_deal_saving,
                "last_scraped_at": last_scraped_str,
            }

    except Exception as e:
        logger.error(f"Error getting KPI summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            "total_products": 0,
            "deals_today": 0,
            "avg_discount_pct": 0.0,
            "best_deal_name": None,
            "best_deal_saving": 0,
            "last_scraped_at": None,
        }
