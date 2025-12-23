import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Create data directory
data_dir = Path(__file__).parent / 'data'
data_dir.mkdir(exist_ok=True)

db_path = data_dir / (os.getenv('DB_FILE', 'app.db'))

def get_db():
    """Get database connection with busy timeout to reduce locking"""
    conn = sqlite3.connect(str(db_path), timeout=5.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Access columns by name
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn

def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    
    migrations = [
        """CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS groups (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_by TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS group_members (
            group_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id)
        )""",
        """CREATE TABLE IF NOT EXISTS expenses (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            description TEXT NOT NULL,
            total_amount REAL NOT NULL,
            paid_by TEXT NOT NULL,
            split_type TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS expense_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            amount REAL,
            percentage REAL
        )""",
        """CREATE TABLE IF NOT EXISTS settlements (
            id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            from_user_id TEXT NOT NULL,
            to_user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            settled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS balances (
            group_id TEXT NOT NULL,
            from_user_id TEXT NOT NULL,
            to_user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            PRIMARY KEY (group_id, from_user_id, to_user_id)
        )""",
        'CREATE INDEX IF NOT EXISTS idx_expenses_group ON expenses(group_id)',
        'CREATE INDEX IF NOT EXISTS idx_splits_expense ON expense_splits(expense_id)',
        'CREATE INDEX IF NOT EXISTS idx_settlements_group ON settlements(group_id)',
        'CREATE INDEX IF NOT EXISTS idx_balances_group ON balances(group_id)'
    ]
    
    for sql in migrations:
        try:
            cursor.execute(sql)
        except sqlite3.Error as e:
            pass  # Table already exists
    
    conn.commit()
    conn.close()
    
    return True
