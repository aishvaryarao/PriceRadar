import sqlite3
conn = sqlite3.connect('priceradar.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM products')
count = cur.fetchone()[0]
print(f'✅ Products in database: {count}')
