import sqlite3
import os

db_path = r"d:\tbook_final\p_12_kb\phy12_examples.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("--- Exact Row for 7.2 ---")
# Query for strictly 7.2
cur.execute("SELECT * FROM examples WHERE example_id='7.2'")
rows = cur.fetchall()
for row in rows:
    print(f"Row: {row}")

print("\n--- Rows for Chapter 7 ---")
cur.execute("SELECT * FROM examples WHERE chapter_name='7'")
rows = cur.fetchall()
print(f"Total Chapter 7 Examples: {len(rows)}")
for row in rows[:3]:
    print(f"Sample: {row}")

conn.close()
