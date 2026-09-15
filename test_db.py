"""Quick test of database connectivity and queries."""
import sys
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

from src.pipeline.loader import get_db_context, USE_SQLITE

print(f"Using SQLite: {USE_SQLITE}")

try:
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Test simple query
        cursor.execute("SELECT COUNT(*) AS cnt FROM products")
        result = cursor.fetchone()
        print(f"✅ Count result type: {type(result)}, value: {result}")
        print(f"✅ Count by index [0]: {result[0]}")
        
        # Test fetching a product
        cursor.execute("SELECT * FROM products LIMIT 1")
        product = cursor.fetchone()
        print(f"✅ Product type: {type(product)}")
        print(f"✅ Product[0]: {product[0]}")
        print(f"✅ Product[1]: {product[1]}")
        
        cursor.close()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

