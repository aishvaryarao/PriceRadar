"""Database loader for product and price data."""
import logging
from contextlib import contextmanager
from typing import Any
from datetime import datetime
from pathlib import Path
import os
import sqlite3

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Try to detect if we're using SQLite fallback
USE_SQLITE = False
SQLITE_DB_PATH = Path(__file__).parent.parent.parent / "priceradar.db"


def _try_postgres_connection():
    """Try to establish PostgreSQL connection."""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            return False
        conn = psycopg2.connect(database_url)
        conn.close()
        return True
    except Exception:
        return False


# Check if PostgreSQL is available, otherwise use SQLite
if not _try_postgres_connection() and SQLITE_DB_PATH.exists():
    USE_SQLITE = True
    logger_init = logging.getLogger(__name__)
    logger_init.info("📦 Using SQLite fallback database")
else:
    logger_init = logging.getLogger(__name__)
    logger_init.info("🐘 Using PostgreSQL database")

logger = logging.getLogger(__name__)


class SQLiteCursorWrapper:
    """Wrapper to make SQLite cursor compatible with psycopg2 cursor interface."""
    
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor
    
    def execute(self, query: str, params: tuple = ()):
        """Execute query, converting PostgreSQL placeholders to SQLite."""
        # Convert %s to ?
        modified_query = query.replace("%s", "?")
        return self.cursor.execute(modified_query, params)
    
    def fetchone(self):
        """Fetch one row."""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Fetch all rows."""
        return self.cursor.fetchall()
    
    def close(self):
        """Close cursor."""
        self.cursor.close()
    
    @property
    def rowcount(self):
        """Get row count."""
        return self.cursor.rowcount
    
    @property
    def lastrowid(self):
        """Get last row ID."""
        return self.cursor.lastrowid


class SQLiteConnectionWrapper:
    """Wrapper to make SQLite connection compatible with psycopg2 connection interface."""
    
    def __init__(self, sqlite_conn):
        self.conn = sqlite_conn
    
    def cursor(self):
        """Get a cursor (wrapped for compatibility)."""
        return SQLiteCursorWrapper(self.conn.cursor())
    
    def commit(self):
        """Commit transaction."""
        self.conn.commit()
    
    def rollback(self):
        """Rollback transaction."""
        self.conn.rollback()
    
    def close(self):
        """Close connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def get_connection():
    """Get database connection from environment or SQLite fallback.

    Returns:
        Database connection (psycopg2 or wrapped sqlite3)

    Raises:
        ValueError: If DATABASE_URL not set and SQLite unavailable
    """
    if USE_SQLITE:
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        logger.debug("SQLite connection established")
        return SQLiteConnectionWrapper(sqlite_conn)
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    try:
        conn = psycopg2.connect(database_url)
        logger.debug("PostgreSQL connection established")
        return conn
    except psycopg2.Error as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        raise


@contextmanager
def get_db_context():
    """Context manager for database connections.

    Yields:
        Database connection (psycopg2 or wrapped sqlite3)

    Example:
        with get_db_context() as conn:
            cursor = conn.cursor()
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def upsert_product(product: dict[str, Any], conn: psycopg2.extensions.connection) -> int:
    """Insert or update product, return product_id.

    Args:
        product: Product data dictionary
        conn: Database connection

    Returns:
        Product ID

    Raises:
        psycopg2.Error: If database error
    """
    if not product.get("url"):
        logger.warning("Product missing URL, skipping upsert")
        return None

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if product exists
        cursor.execute("SELECT id FROM products WHERE url = %s", (product["url"],))
        result = cursor.fetchone()

        if result:
            # Update existing product
            product_id = result["id"]

            update_sql = """
            UPDATE products
            SET name = %s, brand = %s, category = %s, platform = %s,
                image_url = %s, product_id_on_platform = %s,
                rating = %s, review_count = %s, updated_at = NOW()
            WHERE id = %s
            """

            cursor.execute(
                update_sql,
                (
                    product.get("name"),
                    product.get("brand"),
                    product.get("category"),
                    product.get("platform"),
                    product.get("image_url"),
                    product.get("product_id_on_platform"),
                    product.get("rating"),
                    product.get("review_count"),
                    product_id,
                ),
            )

            logger.debug(f"Updated product {product_id}: {product.get('name')}")

        else:
            # Insert new product
            insert_sql = """
            INSERT INTO products (name, brand, category, platform, url, image_url,
                                product_id_on_platform, rating, review_count, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
            """

            cursor.execute(
                insert_sql,
                (
                    product.get("name"),
                    product.get("brand"),
                    product.get("category"),
                    product.get("platform"),
                    product.get("url"),
                    product.get("image_url"),
                    product.get("product_id_on_platform"),
                    product.get("rating"),
                    product.get("review_count"),
                ),
            )

            product_id = cursor.fetchone()["id"]
            logger.debug(f"Inserted product {product_id}: {product.get('name')}")

        cursor.close()
        return product_id

    except psycopg2.Error as e:
        logger.error(f"Error upserting product: {e}")
        raise


def insert_price(
    product_id: int, price_data: dict[str, Any], conn: psycopg2.extensions.connection
) -> bool:
    """Insert price history record.

    Args:
        product_id: Product ID
        price_data: Dictionary with price, original_price, discount_pct, in_stock
        conn: Database connection

    Returns:
        True if successful

    Raises:
        psycopg2.Error: If database error
    """
    try:
        cursor = conn.cursor()

        insert_sql = """
        INSERT INTO price_history (product_id, price, original_price, discount_pct, in_stock, scraped_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """

        cursor.execute(
            insert_sql,
            (
                product_id,
                price_data.get("price"),
                price_data.get("original_price"),
                price_data.get("discount_pct"),
                price_data.get("in_stock", True),
            ),
        )

        cursor.close()
        logger.debug(f"Inserted price for product {product_id}: {price_data.get('price')}")
        return True

    except psycopg2.Error as e:
        logger.error(f"Error inserting price: {e}")
        raise


def load_batch(products: list[dict[str, Any]]) -> dict[str, int]:
    """Load batch of products to database.

    Args:
        products: List of product dictionaries

    Returns:
        Dictionary with counts: inserted, updated, failed
    """
    stats = {"inserted": 0, "updated": 0, "failed": 0}

    try:
        with get_db_context() as conn:
            for product in products:
                try:
                    product_id = upsert_product(product, conn)

                    if product_id:
                        # Insert price history
                        price_data = {
                            "price": product.get("price"),
                            "original_price": product.get("original_price"),
                            "discount_pct": product.get("discount_pct"),
                            "in_stock": True,
                        }

                        insert_price(product_id, price_data, conn)

                        # Increment counter (rough estimate)
                        if product.get("_is_new"):
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1

                except Exception as e:
                    logger.warning(f"Failed to load product: {e}")
                    stats["failed"] += 1

    except Exception as e:
        logger.error(f"Batch load failed: {e}")

    logger.info(f"Batch load complete: {stats}")
    return stats


def refresh_price_summary(conn: psycopg2.extensions.connection) -> bool:
    """Refresh materialized view for price summary.

    Args:
        conn: Database connection

    Returns:
        True if successful

    Raises:
        psycopg2.Error: If refresh fails
    """
    try:
        cursor = conn.cursor()
        cursor.execute("REFRESH MATERIALIZED VIEW price_summary")
        cursor.close()
        logger.info("Refreshed price_summary materialized view")
        return True
    except psycopg2.Error as e:
        logger.error(f"Error refreshing view: {e}")
        raise
