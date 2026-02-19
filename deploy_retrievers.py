
import os
import pathlib

def deploy():
    root = pathlib.Path(r"d:\tbook_final")
    kb_folders = [d for d in root.iterdir() if d.is_dir() and d.name.endswith("_kb")]
    
    # Read the new code from new_retriever_code.py
    new_code_path = root / "new_retriever_code.py"
    if not new_code_path.exists():
        print(f"Error: {new_code_path} not found.")
        return

    with open(new_code_path, "r", encoding="utf-8") as f:
        retriever_code = f.read()

    print(f"Deploying retriever.py to: {[d.name for d in kb_folders]}")
    
    for folder in kb_folders:
        retriever_path = folder / "retriever.py"
        try:
            with open(retriever_path, "w", encoding="utf-8") as f:
                f.write(retriever_code)
            print(f"Updated {retriever_path}")
        except Exception as e:
            print(f"Failed to update {retriever_path}: {e}")

if __name__ == "__main__":
    deploy()
