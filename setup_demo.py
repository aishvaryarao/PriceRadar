"""Quick setup script to initialize SQLite database with sample data."""
from src.database.sqlite_fallback import init_sqlite_db, populate_sqlite_sample_data

if __name__ == "__main__":
    print("🔧 Setting up SQLite database for demonstration...")
    init_sqlite_db()
    if populate_sqlite_sample_data():
        print("✅ Database ready! You can now view sample data in the application.")
    else:
        print("❌ Failed to populate sample data.")
