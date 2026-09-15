import json
import urllib.request

# Test products
print('=== Testing Products ===')
r = urllib.request.urlopen('http://localhost:8000/products?limit=2')
data = json.load(r)
print(f'Got {len(data)} products')

# Test search
print('\n=== Testing Search ===')
r = urllib.request.urlopen('http://localhost:8000/search?q=iPhone')
data = json.load(r)
print(f'Search found {len(data)} products')
for p in data:
    print(f'  {p["name"]} on {p["platform"]}')

# Test price history with different days
print('\n=== Testing Price History ===')
for days in [30, 90, 180]:
    r = urllib.request.urlopen(f'http://localhost:8000/products/1/history?days={days}')
    hist = json.load(r)
    print(f'  {days}d: {len(hist)} records')

