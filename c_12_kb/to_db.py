import sqlite3
import re


# ===============================
# 1️⃣ TOPICS DB
# ===============================
def topics_to_db():
    conn = sqlite3.connect("topics.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        topic_number TEXT,
        topic_title TEXT,
        description TEXT
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
            INSERT INTO topics (chapter_name, topic_number, topic_title, description)
            VALUES (?, ?, ?, ?)
            """, (current_chapter, match.group(1), match.group(3), None))

    conn.commit()
    conn.close()
    print("topics.db ✅")


# ===============================
# 2️⃣ EXERCISE DB
# ===============================
def exercise_to_db():
    conn = sqlite3.connect("exercise.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        q_id TEXT,
        question TEXT
    )
    """)

    with open("questions.txt", "r", encoding="utf-8") as f:
        content = f.read()

    chapters = re.split(r"=+\s*CHAPTER\s*\d+\s*=+", content)

    for block in chapters[1:]:
        lines = block.strip().split("\n")
        chapter_name = lines[0].strip()

        matches = re.finditer(r"(\d+\.\d+)\s+(.*?)(?=\n\d+\.\d+|\Z)", block, re.S)

        for m in matches:
            q_id = m.group(1)
            question = m.group(2).strip().replace("\n", " ")

            cur.execute("""
            INSERT INTO exercise (chapter_name, q_id, question)
            VALUES (?, ?, ?)
            """, (chapter_name, q_id, question))

    conn.commit()
    conn.close()
    print("exercise.db ✅")


# ===============================
# 3️⃣ PROBLEMS DB
# ===============================
def problems_to_db():
    conn = sqlite3.connect("problems.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        question TEXT,
        solution_preview TEXT
    )
    """)

    with open("examples.txt", "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.finditer(
        r"Example\s+(\d+\.\d+)\s*\nQ:\s*(.*?)\nFirst 1000 chars of Solution:\s*(.*?)(?=\nExample|\Z)",
        content,
        re.S,
    )

    for m in matches:
        chp = m.group(1).split(".")[0]
        question = m.group(2).strip()
        solution = m.group(3).strip()[:1000]

        cur.execute("""
        INSERT INTO problems (chapter_name, question, solution_preview)
        VALUES (?, ?, ?)
        """, (chp, question, solution))

    conn.commit()
    conn.close()
    print("problems.db ✅")


# ===============================
# 4️⃣ INTEXT DB
# ===============================
def intext_to_db():
    conn = sqlite3.connect("intext.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS intext (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        q_id TEXT,
        question TEXT
    )
    """)

    with open("intext.txt", "r", encoding="utf-8") as f:
        content = f.read()

    matches = re.finditer(r"(\d+\.\d+)\s+(.*?)(?=\n\d+\.\d+|\Z)", content, re.S)

    for m in matches:
        chp = m.group(1).split(".")[0]
        q_id = m.group(1)
        question = m.group(2).strip().replace("\n", " ")

        cur.execute("""
        INSERT INTO intext (chapter_name, q_id, question)
        VALUES (?, ?, ?)
        """, (chp, q_id, question))

    conn.commit()
    conn.close()
    print("intext.db ✅")


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    topics_to_db()
    exercise_to_db()
    problems_to_db()
    intext_to_db()
