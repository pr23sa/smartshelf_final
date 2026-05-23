import sqlite3
from datetime import datetime

conn = sqlite3.connect("smartshelf.db")
cur = conn.cursor()

# Check all tables
print("=== ALL TABLES ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cur.fetchall())

# Check borrows table structure
print("\n=== BORROWS TABLE COLUMNS ===")
cur.execute("PRAGMA table_info(borrows)")
print(cur.fetchall())

# Check all rows in borrows
print("\n=== ALL BORROWS ROWS ===")
cur.execute("SELECT * FROM borrows")
rows = cur.fetchall()
print(f"Total rows: {len(rows)}")
for r in rows:
    print(r)

# Check reservations table if exists
print("\n=== RESERVATIONS TABLE IF EXISTS ===")
try:
    cur.execute("SELECT * FROM reservations")
    print(cur.fetchall())
except Exception as e:
    print(f"No reservations table: {e}")

# Check books table
print("\n=== BOOKS SAMPLE ===")
cur.execute("SELECT id, title FROM books LIMIT 5")
print(cur.fetchall())

conn.close()
