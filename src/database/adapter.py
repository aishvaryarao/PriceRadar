"""Database adapter to support both PostgreSQL and SQLite."""
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

SQLITE_DB_PATH = Path(__file__).parent.parent.parent / "priceradar.db"


class DatabaseAdapter:
    """Adapter to work with both PostgreSQL and SQLite databases."""
    
    def __init__(self):
        """Initialize the adapter, detecting which database is available."""
        self.is_sqlite = False
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        
        if SQLITE_DB_PATH.exists():
            self.is_sqlite = True
            self.sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info("📦 Using SQLite database adapter")
        else:
            logger.info("🐘 Using PostgreSQL database adapter")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a SELECT query and return results as list of dicts."""
        if self.is_sqlite:
            cur = self.sqlite_conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        return []
    
    def execute_single(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute a SELECT query and return single result."""
        if self.is_sqlite:
            cur = self.sqlite_conn.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
        return None
    
    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT query and return inserted ID."""
        if self.is_sqlite:
            cur = self.sqlite_conn.cursor()
            cur.execute(query, params)
            self.sqlite_conn.commit()
            return cur.lastrowid
        return 0
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute UPDATE query and return rows affected."""
        if self.is_sqlite:
            cur = self.sqlite_conn.cursor()
            cur.execute(query, params)
            self.sqlite_conn.commit()
            return cur.rowcount
        return 0


# Global adapter instance
_adapter: Optional[DatabaseAdapter] = None


def get_adapter() -> DatabaseAdapter:
    """Get or create database adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = DatabaseAdapter()
    return _adapter
