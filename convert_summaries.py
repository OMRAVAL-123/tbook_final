
import sqlite3
import pathlib
import os

def convert():
    root = pathlib.Path(r"d:\tbook_final")
    kb_folders = [d for d in root.iterdir() if d.is_dir() and d.name.endswith("_kb")]
    
    for folder in kb_folders:
        db_path = folder / "summaries.db"
        txt_path = folder / "summaries.txt"
        
        if db_path.exists():
            print(f"Processing {folder.name}...")
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT chapter_no, chapter_title, summary FROM summaries")
                rows = cursor.fetchall()
                conn.close()
                
                with open(txt_path, "w", encoding="utf-8") as f:
                    for r in rows:
                        # Format: Chapter X: Title \n Summary \n\n
                        f.write(f"Chapter {r[0]}: {r[1]}\n")
                        f.write(f"{r[2].strip()}\n")
                        f.write("-" * 40 + "\n")
                
                print(f"Created {txt_path} with {len(rows)} summaries.")
            except Exception as e:
                print(f"Error reading {db_path}: {e}")
        else:
            print(f"No summaries.db in {folder.name}")

if __name__ == "__main__":
    convert()
