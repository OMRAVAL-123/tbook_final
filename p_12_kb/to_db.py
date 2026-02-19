import sqlite3
import re


# =====================================
# 1️⃣ TOPICS
# =====================================
def topics_to_db():
    conn = sqlite3.connect("phy12_topics.db")
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

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.lower().startswith("unit"):
            current_chapter = line
            continue

        match = re.match(r"^(\d+(\.\d+)*)\s+(.*)", line)
        if match:
            cur.execute("""
            INSERT INTO topics (chapter_name, topic_number, topic_title)
            VALUES (?, ?, ?)
            """, (current_chapter, match.group(1), match.group(3)))

    conn.commit()
    conn.close()
    print("phy12_topics.db ✅")


# =====================================
# 2️⃣ EXERCISES
# =====================================
def exercise_to_db():
    conn = sqlite3.connect("phy12_exercise.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        q_id TEXT,
        question TEXT
    )
    """)

    with open("exercises.txt", "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.finditer(
        r"Question\s+(\d+\.\d+)\s*(.*?)\n(?=Question|\Z)",
        content,
        re.S
    )

    for m in matches:
        q_id = m.group(1)
        question = m.group(2).strip().replace("\n", " ")
        chapter_name = q_id.split(".")[0]

        cur.execute("""
        INSERT INTO exercise (chapter_name, q_id, question)
        VALUES (?, ?, ?)
        """, (chapter_name, q_id, question))

    conn.commit()
    conn.close()
    print("phy12_exercise.db ✅")


# =====================================
# 3️⃣ EXAMPLES
# =====================================
def examples_to_db():
    conn = sqlite3.connect("phy12_examples.db")
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

    matches = re.finditer(
        r"Example\s+(\d+\.\d+)\s*\nQuestion:\s*(.*?)\nFirst 1000 chars of Solution:\s*(.*?)(?=Example|\Z)",
        content,
        re.S
    )

    for m in matches:
        ex_id = m.group(1)
        question = m.group(2).strip().replace("\n", " ")
        solution = m.group(3).strip()[:1000]
        chapter_name = ex_id.split(".")[0]

        cur.execute("""
        INSERT INTO examples (chapter_name, example_id, question, solution_preview)
        VALUES (?, ?, ?, ?)
        """, (chapter_name, ex_id, question, solution))

    conn.commit()
    conn.close()
    print("phy12_examples.db ✅")


# =====================================
# MAIN
# =====================================
if __name__ == "__main__":
    topics_to_db()
    exercise_to_db()
    examples_to_db()
