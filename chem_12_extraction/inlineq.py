import fitz
import re
from tqdm import tqdm

PDF_PATH = "Chemistry-12.pdf"
OUTPUT_FILE = "c_12_kb/intext_questions.txt"

question_pattern = re.compile(r"^\d+\.\d+$")

doc = fitz.open(PDF_PATH)

all_questions = []
intext_mode = False
current_question = None

def is_intext_heading(span):
    return (
        span["font"] == "BallroomTango"
        and round(span["size"]) == 13
        and "Intext" in span["text"]
    )

def is_question_number(span):
    return (
        span["font"] == "Bookman-Demi"
        and round(span["size"], 1) == 10.5
        and question_pattern.match(span["text"].strip())
    )

def is_question_text(span):
    return (
        span["font"] == "Bookman-Light"
        and round(span["size"], 1) == 10.5
    )

for page_num in tqdm(range(len(doc)), desc="Scanning PDF"):
    page = doc[page_num]
    text_dict = page.get_text("dict")

    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            for span in line["spans"]:

                text = span["text"].strip()

                if not text:
                    continue

                # 1️⃣ Detect Intext Section Start
                if is_intext_heading(span):
                    intext_mode = True
                    continue

                if not intext_mode:
                    continue

                # 2️⃣ Detect New Question Number
                if is_question_number(span):

                    # Save previous question
                    if current_question:
                        all_questions.append(current_question.strip())

                    current_question = text
                    continue

                # 3️⃣ Collect Question Body
                if current_question and is_question_text(span):
                    current_question += " " + text

                # 4️⃣ Stop if new big section starts
                if span["font"] == "BallroomTango" and round(span["size"]) >= 14:
                    intext_mode = False

# Save last question
if current_question:
    all_questions.append(current_question.strip())

# Write to file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for q in all_questions:
        f.write(q + "\n\n")

print(f"✅ Extracted {len(all_questions)} Intext Questions")
print("Saved to:", OUTPUT_FILE)
