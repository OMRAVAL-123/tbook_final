import os
import sys
import re
import fitz
from tqdm import tqdm

pdf_path = "dataset/Mathematics-12.pdf"
doc = fitz.open(pdf_path)

os.makedirs("m_12_kb", exist_ok=True)

# ===============================
# BLUE COLOR CHECK
# ===============================

def is_blue(color):
    r = (color >> 16) & 255
    g = (color >> 8) & 255
    b = color & 255
    return (r, g, b) in [(0,174,239), (0,185,242)]

# ===============================
# 1️⃣ TOPICS EXTRACTION
# ===============================

def extract_topics():
    output = []

    for page in tqdm(doc, desc="Extracting Topics"):
        data = page.get_text("dict")

        for block in data["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                text = ""
                fonts = []
                sizes = []
                colors = []

                for span in line["spans"]:
                    text += span["text"]
                    fonts.append(span["font"])
                    sizes.append(round(span["size"],2))
                    colors.append(span["color"])

                text = re.sub(r"\s+", " ", text).strip()
                if not text:
                    continue

                # Only blue + bold
                if not any(is_blue(c) for c in colors):
                    continue
                if not any("Bold" in f for f in fonts):
                    continue

                # Chapter title
                if any(s >= 22 for s in sizes):
                    output.append(text)
                    continue

                # Section format 1. 1.1 1.1.1
                if re.match(r"^\d+(\.\d+)+", text):
                    output.append(text)
                    continue

                # Misc / Summary
                if "Miscellaneous" in text or "Summary" in text:
                    output.append(text)
                    continue

    with open("m_12_kb/topics.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))


# ===============================
# 2️⃣ EXAMPLES EXTRACTION
# ===============================
def extract_examples():
    output = []
    chapter_counter = 1
    current_example = None
    question = ""
    solution = ""
    state = "idle"
    first_example_seen = False

    for page in tqdm(doc, desc="Extracting Examples"):
        data = page.get_text("dict")

        for block in data["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                full_text = ""
                colors = []

                for span in line["spans"]:
                    full_text += span["text"]
                    colors.append(span["color"])

                full_text = re.sub(r"\s+", " ", full_text).strip()
                if not full_text:
                    continue

                is_blue_line = any(is_blue(c) for c in colors)

                # ===== Detect Example =====
                if is_blue_line and full_text.startswith("Example"):

                    # Save previous example first
                    if current_example:
                        output.append(f"Chapter {chapter_counter} - {current_example}")
                        output.append("Question: " + question.strip())
                        output.append("First 1000 chars of Solution:")
                        output.append(solution[:1000])
                        output.append("-" * 80)
                        output.append("")

                    # Extract example number
                    match = re.match(r"Example\s+(\d+)", full_text)
                    if match:
                        example_number = match.group(1)

                        # Increment chapter ONLY if:
                        # Example 1 appears again AND not first overall example
                        if example_number == "1":
                            if first_example_seen:
                                chapter_counter += 1
                            else:
                                first_example_seen = True

                    current_example = full_text
                    question = ""
                    solution = ""
                    state = "question"
                    continue

                # ===== Detect Solution label =====
                if is_blue_line and full_text.startswith("Solution"):
                    state = "solution"
                    continue

                # ===== Capture Text =====
                if state == "question":
                    question += " " + full_text
                elif state == "solution":
                    solution += " " + full_text

    # Save last example
    if current_example:
        output.append(f"Chapter {chapter_counter} - {current_example}")
        output.append("Question: " + question.strip())
        output.append("First 1000 chars of Solution:")
        output.append(solution[:1000])
        output.append("-" * 80)

    with open("m_12_kb/examples.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

# ===============================
# 3️⃣ Data EXTRACTION
# ===============================
import pytesseract
from PIL import Image

def extract_ocr_data():
    all_text = []

    for page in tqdm(doc, desc="OCR Extracting"):
        rect = page.rect
        header = rect.height * 0.08
        footer = rect.height * 0.08
        clip = fitz.Rect(rect.x0, rect.y0 + header, rect.x1, rect.y1 - footer)

        pix = page.get_pixmap(dpi=300, clip=clip)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        text = pytesseract.image_to_string(img, config="--oem 1 --psm 6")
        all_text.append(text)

    with open("m_12_kb/data.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))

# ===============================
# RUN ALL
# ===============================

extract_topics()
extract_examples()
extract_ocr_data()

print("✅ Maths 12 BLUE engine complete.")
