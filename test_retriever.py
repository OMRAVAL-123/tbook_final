import sys
import os
import traceback

sys.path.append(r"d:\tbook_final\m_12_kb")
import retriever

try:
    res = retriever.retrieve("Example 7.2")
    print("MATH 12 - Example 7.2 Result:")
    print(res['answer'])
except Exception as e:
    print("Error during retrieval:")
    traceback.print_exc()

print("-" * 50)

try:
    res2 = retriever.retrieve("Example 1.2")
    print("MATH 12 - Example 1.2 Result:")
    print(res2['answer'])
except Exception as e:
    print("Error during retrieval 2:")
    traceback.print_exc()
