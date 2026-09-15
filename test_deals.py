#!/usr/bin/env python
"""Test the deals endpoint."""
from src.analytics.queries import get_top_deals

# Test get_top_deals first
df = get_top_deals(limit=50)
print(f"get_top_deals returned {len(df)} rows")
if len(df) > 0:
    print("Columns:", df.columns.tolist())
    print(f"First deal: {df.iloc[0]['name']} - drop: {df.iloc[0]['drop_from_max_pct']}%")
    print("\nFirst 3 deals:")
    for idx, row in df.head(3).iterrows():
        print(f"  {row['name']}: {row['drop_from_max_pct']}% drop")

