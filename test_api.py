"""Test API endpoint directly."""
import sys
sys.path.insert(0, str(__file__).rsplit('\\', 2)[0])

from src.api.main import list_products
import asyncio

async def test():
    try:
        result = await list_products()
        print(f"✅ API returned: {len(result)} products")
        if result:
            print(f"First product: {result[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
