import sqlite3
import re
import os


# ==============================
# 1️⃣ TOPICS DB
# ==============================
def topics_to_db(txt_path="topics.txt", db_name="topics.db"):
    conn = sqlite3.connect(db_name)
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

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_chapter = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect UNIT / Unit as chapter
        if line.lower().startswith("unit"):
            current_chapter = line
            continue

        # Detect topic like 1.2 or 1.2.1
        match = re.match(r"^(\d+(\.\d+)*)\s+(.*)", line)
        if match:
            topic_no = match.group(1)
            topic_title = match.group(3)

            cur.execute("""
            INSERT INTO topics (chapter_name, topic_number, topic_title, description)
            VALUES (?, ?, ?, ?)
            """, (current_chapter, topic_no, topic_title, None))

    conn.commit()
    conn.close()
    print("topics.db created ✅")


# ==============================
# 2️⃣ EXERCISE DB
# ==============================
def exercise_to_db(txt_path="exercise.txt", db_name="exercise.db"):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercise (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        question_no TEXT,
        question TEXT
    )
    """)

    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Detect chapters
    chapters = re.split(r"\n=+\n", content)

    for chapter_block in chapters:
        lines = chapter_block.strip().split("\n")
        if not lines:
            continue

        chapter_name = lines[0].strip()

        # Find exercises
        matches = re.finditer(r"Exercise\s+([\d\.]+)\s*\n(.*?)(?=\nExercise|\Z)", chapter_block, re.S)

        for m in matches:
            q_no = m.group(1).strip()
            question = m.group(2).strip().replace("\n", " ")

            cur.execute("""
            INSERT INTO exercise (chapter_name, question_no, question)
            VALUES (?, ?, ?)
            """, (chapter_name, q_no, question))

    conn.commit()
    conn.close()
    print("exercise.db created ✅")


# ==============================
# 3️⃣ PROBLEMS DB
# ==============================
def problems_to_db(txt_path="problems.txt", db_name="problems.db"):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chapter_name TEXT,
        question TEXT,
        solution_preview TEXT
    )
    """)

    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by Problem X.X
    problems = re.split(r"Problem\s+\d+\.\d+", content)

    headers = re.findall(r"Problem\s+(\d+\.\d+)", content)

    for idx, block in enumerate(problems[1:]):
        question_match = re.search(r"Q:\s*(.*?)\n", block)
        solution_match = re.search(r"First 1000 chars of Solution:\s*(.*)", block, re.S)

        question = question_match.group(1).strip() if question_match else None
        solution = solution_match.group(1).strip() if solution_match else None

        if solution:
            solution = solution[:1000]

        chapter_name = headers[idx].split(".")[0] if idx < len(headers) else None

        cur.execute("""
        INSERT INTO problems (chapter_name, question, solution_preview)
        VALUES (?, ?, ?)
        """, (chapter_name, question, solution))

    conn.commit()
    conn.close()
    print("problems.db created ✅")


# ==============================
# MAIN RUN
# ==============================
if __name__ == "__main__":
    topics_to_db("topics.txt", "topics.db")
    exercise_to_db("exercise.txt", "exercise.db")
    problems_to_db("problems.txt", "problems.db")
