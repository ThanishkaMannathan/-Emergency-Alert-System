"""
init_db.py  –  Run this once to create the SQLite database.
Usage:  python init_db.py
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "alerts.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude  REAL    NOT NULL,
        longitude REAL    NOT NULL,
        maps_link TEXT    NOT NULL,
        address   TEXT,
        timestamp TEXT    NOT NULL,
        status    TEXT    DEFAULT 'sent'
    )
""")

conn.commit()
conn.close()
print(f"✅  Database created at: {DB_PATH}")
print("    Table 'alerts' is ready.")
