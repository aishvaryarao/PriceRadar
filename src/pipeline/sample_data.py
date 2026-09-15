"""Sample data generator for demonstration and testing."""
import logging
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv
import os
import random

load_dotenv()

logger = logging.getLogger(__name__)


def populate_sample_data():
    """Populate database with sample products and price history for testing."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    
    sample_products = [
        {"name": "iPhone 15 Pro Max", "platform": "Amazon", "category": "smartphones", "price": 129999, "rating": 4.5},
        {"name": "Samsung Galaxy S25 Ultra", "platform": "Flipkart", "category": "smartphones", "price": 119999, "rating": 4.7},
        {"name": "OnePlus 12", "platform": "Amazon", "category": "smartphones", "price": 69999, "rating": 4.3},
        {"name": "MacBook Pro 16 M3", "platform": "Amazon", "category": "laptops", "price": 249999, "rating": 4.8},
        {"name": "Dell XPS 13 Plus", "platform": "Flipkart", "category": "laptops", "price": 119999, "rating": 4.4},
        {"name": "Sony WH-1000XM5 Headphones", "platform": "Amazon", "category": "headphones", "price": 29999, "rating": 4.6},
        {"name": "Bose QuietComfort 45", "platform": "Flipkart", "category": "headphones", "price": 34999, "rating": 4.5},
        {"name": "Nivea Face Wash", "platform": "Amazon", "category": "face wash", "price": 299, "rating": 4.2},
        {"name": "Cetaphil Gentle Cleanser", "platform": "Flipkart", "category": "face wash", "price": 599, "rating": 4.3},
        {"name": "Optimum Nutrition Whey Protein", "platform": "Amazon", "category": "protein powder", "price": 2499, "rating": 4.4},
        {"name": "MyProtein Impact Whey", "platform": "Flipkart", "category": "protein powder", "price": 2199, "rating": 4.1},
    ]
    
    try:
        # Insert products
        inserted_ids = []
        for product in sample_products:
            cur.execute("""
                INSERT INTO products (name, platform, category, current_price, rating, scraped_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (name, platform) DO UPDATE 
                SET current_price = EXCLUDED.current_price, rating = EXCLUDED.rating
                RETURNING id;
            """, (product["name"], product["platform"], product["category"], product["price"], product["rating"]))
            product_id = cur.fetchone()[0]
            inserted_ids.append((product_id, product["price"]))
        
        # Insert price history (simulate 30 days of data)
        for product_id, base_price in inserted_ids:
            for days_ago in range(30):
                # Simulate price fluctuations
                price_variance = random.uniform(0.95, 1.05)
                price = int(base_price * price_variance)
                price_date = datetime.now() - timedelta(days=days_ago)
                
                cur.execute("""
                    INSERT INTO price_history (product_id, price, scraped_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (product_id, DATE(scraped_at)) DO NOTHING;
                """, (product_id, price, price_date))
        
        conn.commit()
        logger.info(f"✅ Inserted {len(sample_products)} sample products with 30 days of price history")
        print(f"✅ Successfully populated database with {len(sample_products)} sample products!")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Failed to populate sample data: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    populate_sample_data()
