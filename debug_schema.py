import sqlite3
import pathlib
import os

base_path = pathlib.Path(r"d:\tbook_final\p_12_kb")
dbs = list(base_path.glob("*.db"))

print(f"DBs found: {dbs}")

def _load_schemas(dbs):
    schemas = {}
    for db_path in dbs:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            db_schema_str = []
            for table in tables:
                table_name = table[0]
                if table_name.startswith("sqlite_"): continue
                
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                col_str = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
                
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    # Fetch one sample row
                    rows = cursor.fetchall()
                    sample_str = f"Sample rows: {str(rows)}"
                except:
                    sample_str = "No samples available."
                    
                db_schema_str.append(f"Table: {table_name}\nColumns: {col_str}\n{sample_str}")
            
            if db_schema_str:
                schemas[db_path.name] = "\n\n".join(db_schema_str)
            conn.close()
        except Exception as e:
            print(f"Error loading schema for {db_path}: {e}")
    return schemas

schemas = _load_schemas(dbs)
print("\n--- GENERATED PROMPT CONTEXT ---")
full_schema_context = ""
for db_file, schema in schemas.items():
    full_schema_context += f"Database File: {db_file}\n{schema}\n\n"
print(full_schema_context)
