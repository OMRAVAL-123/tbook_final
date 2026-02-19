import sqlite3
import os

db_path = r"d:\tbook_final\p_12_kb\phy12_examples.db"
print(f"Checking DB: {db_path}")

if not os.path.exists(db_path):
    print("DB file not found!")
    exit()

try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. Get Table Name
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print(f"Tables found: {tables}")
    
    if not tables:
        print("No tables found.")
        exit()
        
    table_name = tables[0][0]
    print(f"Target Table: {table_name}")

    # 2. Get Schema
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = cur.fetchall()
    print(f"\nSchema for {table_name}:")
    for c in cols:
        print(c)

    # 3. Dump First 10 Rows to understand content format
    print(f"\n--- First 10 Rows in {table_name} ---")
    cur.execute(f"SELECT * FROM {table_name} LIMIT 10")
    rows = cur.fetchall()
    for row in rows:
        print(row)

    # 4. Search for '7.2' specifically
    print("\n--- Searching for '7.2' in all columns ---")
    cur.execute(f"SELECT * FROM {table_name} WHERE example_id LIKE '%7.2%' OR question LIKE '%7.2%' OR solution_preview LIKE '%7.2%'")
    rows = cur.fetchall()
    if rows:
        print(f"Found {len(rows)} matches for '7.2':")
        for row in rows:
            print(row)
    else:
        print("No direct matches for '7.2'.")

    # 5. Check Chapter 7 existence
    print("\n--- Checking for 'Chapter 7' (or similar) ---")
    cur.execute(f"SELECT DISTINCT chapter_name FROM {table_name} WHERE chapter_name LIKE '%7%'")
    chaps = cur.fetchall()
    print(f"Chapters matching '%7%': {chaps}")

    conn.close()

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
