
import sys
import os
import pathlib

# Add p_12_kb to path to import retriever
sys.path.append(str(pathlib.Path(r"d:\tbook_final\p_12_kb")))
import retriever

def test():
    queries = [
        "give me summary of chapter 6 of 12th physics"
    ]
    
    print("--- STARTING TESTS ---")
    for q in queries:
        print(f"\nQuery: '{q}'")
        try:
            res = retriever.retrieve(q)
            print(f"Intent: {res.get('intent')}")
            # Truncate answer
            ans = res.get('answer', '')
            print(f"Answer: {ans[:200]}..." if len(ans) > 200 else f"Answer: {ans}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test()
