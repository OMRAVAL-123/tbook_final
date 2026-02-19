import sqlite3
import os

db_path = r"d:\tbook_final\p_12_kb\phy12_examples.db"

if not os.path.exists(db_path):
    print("DB does not exist")
    exit()

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f"Tables: {tables}")

# Get columns for 'examples'
table_name = tables[0][0] # assume first table is the one we want if 'examples'
print(f"Inspecting table: {table_name}")
cur.execute(f"PRAGMA table_info({table_name})")
cols = cur.fetchall()
print(f"Columns: {cols}")

print("\n--- Rows matching 7.2 in any column ---")
# Try to find 7.2 anywhere
query = f"SELECT * FROM {table_name} WHERE example_id LIKE '%7.2%' OR question LIKE '%7.2%'"
try:
    cur.execute(query)
    rows = cur.fetchall()
    for row in rows:
        print(row)
except Exception as e:
    print(f"Query 1 failed: {e}")

print("\n--- Rows matching Chapter 7 ---")
query = f"SELECT * FROM {table_name} WHERE chapter_name LIKE '%Chapter 7%'" 
try:
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Found {len(rows)} entries for Chapter 7.")
    for row in rows[:5]:
        print(row)
except Exception as e:
    print(f"Query 2 failed: {e}")

conn.close()
