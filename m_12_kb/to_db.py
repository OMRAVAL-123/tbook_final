import sqlite3
import re


# =====================================
# 1️⃣ TOPICS DB
# =====================================
def topics_to_db():
    conn = sqlite3.connect("math12_topics.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        topic_number TEXT,
        topic_title TEXT
    )
    """)

    with open("topics.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_chapter = None
    chapter_counter = 1

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect chapter titles (ALL CAPS headings)
        if line.isupper():
            current_chapter = f"Chapter {chapter_counter} - {line}"
            chapter_counter += 1
            continue

        # Detect numbered topics
        match = re.match(r"^(\d+(\.\d+)*)\s+(.*)", line)
        if match and current_chapter:
            cur.execute("""
            INSERT INTO topics (chapter_name, topic_number, topic_title)
            VALUES (?, ?, ?)
            """, (current_chapter, match.group(1), match.group(3)))

    conn.commit()
    conn.close()
    print("math12_topics.db ✅")


# =====================================
# 2️⃣ EXAMPLES DB
# =====================================
def examples_to_db():
    conn = sqlite3.connect("math12_examples.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        example_id TEXT,
        question TEXT,
        solution_preview TEXT
    )
    """)

    with open("examples.txt", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.finditer(
        r"Chapter\s+(\d+)\s*-\s*Example\s+(\d+)\s*(.*?)Question:\s*(.*?)\nFirst 1000 chars of Solution:\s*(.*?)(?=Chapter|\Z)",
        content,
        re.S
    )

    for m in pattern:
        chapter_name = f"Chapter {m.group(1)}"
        example_id = m.group(2)
        question = m.group(4).strip().replace("\n", " ")
        solution = m.group(5).strip()[:1000]

        cur.execute("""
        INSERT INTO examples (chapter_name, example_id, question, solution_preview)
        VALUES (?, ?, ?, ?)
        """, (chapter_name, example_id, question, solution))

    conn.commit()
    conn.close()
    print("math12_examples.db ✅")


# =====================================
# MAIN
# =====================================
if __name__ == "__main__":
    topics_to_db()
    examples_to_db()
