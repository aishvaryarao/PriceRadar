"""SQLite database fallback for development and testing without Docker/PostgreSQL."""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "priceradar.db"


def init_sqlite_db():
    """Initialize SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            platform TEXT NOT NULL,
            category TEXT,
            current_price REAL,
            rating REAL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, platform)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL,
            scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS deal_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            alert_type TEXT,
            threshold REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    
    conn.commit()
    logger.info(f"✅ SQLite database initialized at {DB_PATH}")
    return conn


def populate_sqlite_sample_data():
    """Populate SQLite with sample data for demonstration."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    sample_products = [
        ("iPhone 15 Pro Max", "Amazon", "smartphones", 129999, 4.5),
        ("Samsung Galaxy S25 Ultra", "Flipkart", "smartphones", 119999, 4.7),
        ("OnePlus 12", "Amazon", "smartphones", 69999, 4.3),
        ("MacBook Pro 16 M3", "Amazon", "laptops", 249999, 4.8),
        ("Dell XPS 13 Plus", "Flipkart", "laptops", 119999, 4.4),
        ("Sony WH-1000XM5 Headphones", "Amazon", "headphones", 29999, 4.6),
        ("Bose QuietComfort 45", "Flipkart", "headphones", 34999, 4.5),
        ("Nivea Face Wash", "Amazon", "face wash", 299, 4.2),
        ("Cetaphil Gentle Cleanser", "Flipkart", "face wash", 599, 4.3),
        ("Optimum Nutrition Whey Protein", "Amazon", "protein powder", 2499, 4.4),
        ("MyProtein Impact Whey", "Flipkart", "protein powder", 2199, 4.1),
    ]
    
    inserted_count = 0
    try:
        for name, platform, category, price, rating in sample_products:
            cur.execute("""
                INSERT OR IGNORE INTO products (name, platform, category, current_price, rating, scraped_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, platform, category, price, rating))
            
            # Get product ID
            cur.execute("SELECT id FROM products WHERE name = ? AND platform = ?", (name, platform))
            product_id = cur.fetchone()[0]
            
            # Insert price history for 30 days
            for days_ago in range(30):
                price_variance = random.uniform(0.95, 1.05)
                price_point = int(price * price_variance)
                price_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
                
                cur.execute("""
                    INSERT INTO price_history (product_id, price, scraped_at)
                    VALUES (?, ?, ?)
                """, (product_id, price_point, price_date))
            
            inserted_count += 1
        
        conn.commit()
        logger.info(f"✅ Populated SQLite with {inserted_count} sample products")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Failed to populate SQLite: {e}")
        return False
    finally:
        cur.close()


def get_sqlite_connection():
    """Get SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
