import sqlite3
import re


# =====================================
# 1️⃣ TOPICS
# =====================================
def topics_to_db():
    conn = sqlite3.connect("math11_topics.db")
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

        # Detect new major chapter headings
        if re.match(r"^\d+\.\d+", line):
            topic_match = re.match(r"^(\d+\.\d+)\s+(.*)", line)
            if topic_match:
                cur.execute("""
                INSERT INTO topics (chapter_name, topic_number, topic_title)
                VALUES (?, ?, ?)
                """, (f"Chapter {chapter_counter}",
                      topic_match.group(1),
                      topic_match.group(2)))
        elif line.isupper():
            chapter_counter += 1

    conn.commit()
    conn.close()
    print("math11_topics.db ✅")


# =====================================
# 2️⃣ EXAMPLES
# =====================================
def examples_to_db():
    conn = sqlite3.connect("math11_examples.db")
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
        r"Chapter\s+(\d+)\s*-\s*Example\s+(\d+)\s*.*?Question:\s*(.*?)\nFirst 1000 chars of Solution:\s*(.*?)(?=Chapter|\Z)",
        content,
        re.S
    )

    for m in pattern:
        chapter_name = f"Chapter {m.group(1)}"
        example_id = m.group(2)
        question = m.group(3).strip().replace("\n", " ")
        solution = m.group(4).strip()[:1000]

        cur.execute("""
        INSERT INTO examples (chapter_name, example_id, question, solution_preview)
        VALUES (?, ?, ?, ?)
        """, (chapter_name, example_id, question, solution))

    conn.commit()
    conn.close()
    print("math11_examples.db ✅")


# =====================================
# MAIN
# =====================================
if __name__ == "__main__":
    topics_to_db()
    examples_to_db()
