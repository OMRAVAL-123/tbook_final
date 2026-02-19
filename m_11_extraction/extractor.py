import os
import sys
import re
import fitz
import pytesseract
from PIL import Image
from tqdm import tqdm

pdf_path = "dataset/Mathematics-11.pdf"
doc = fitz.open(pdf_path)

os.makedirs("m_11_kb", exist_ok=True)

# =====================================================
# 1️⃣ FULL BOOK TOPICS EXTRACTION
# =====================================================
def extract_topics_full_book():
    output = []

    def is_blue(color):
        r = (color >> 16) & 255
        g = (color >> 8) & 255
        b = color & 255
        return (r, g, b) in [(0, 185, 242), (0, 174, 239)]

    for page in doc:
        data = page.get_text("dict")

        for block in data["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_text = ""
                fonts = []
                sizes = []
                colors = []

                for span in line["spans"]:
                    line_text += span["text"]
                    fonts.append(span["font"])
                    sizes.append(round(span["size"], 2))
                    colors.append(span["color"])

                line_text = re.sub(r"\s+", " ", line_text).strip()
                if not line_text:
                    continue

                # Must be blue
                if not any(is_blue(c) for c in colors):
                    continue

                # Must be bold
                if not any("Bold" in f for f in fonts):
                    continue

                # Chapter title (big blue)
                if any(s >= 22 for s in sizes):
                    output.append(line_text)
                    continue

                # Section titles like 1.1, 2.3
                if re.match(r"^\d+\.\d+\s+", line_text):
                    output.append(line_text)
                    continue

                # Miscellaneous / Summary
                if "Miscellaneous" in line_text or "Summary" in line_text:
                    output.append(line_text)
                    continue

    with open("m_11_kb/topics.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

# =====================================================
# 2️⃣ OCR BODY TEXT EXTRACTION
# =====================================================

def extract_information_text():
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

    with open("m_11_kb/information.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(all_text))


# =====================================================
# 3️⃣ EXAMPLES WITH AUTO CHAPTER COUNTER
# =====================================================
def extract_examples_auto_chapter():
    output = []
    chapter_counter = 1
    current_example = None
    question = ""
    solution = ""
    state = "idle"
    first_example_seen = False

    for page in doc:
        text = page.get_text()
        lines = text.split("\n")

        for line in lines:
            line = re.sub(r"\s+", " ", line).strip()
            if not line:
                continue

            match = re.match(r"(Example\s+(\d+))(.*)", line)

            if match:
                example_label = match.group(1)
                example_number = match.group(2)

                # Save previous example FIRST
                if current_example:
                    output.append(f"Chapter {chapter_counter} - {current_example}")
                    output.append("Question: " + question.strip())
                    output.append("First 1000 chars of Solution:")
                    output.append(solution[:1000])
                    output.append("-" * 80)
                    output.append("")

                # Now increment chapter if new Example 1 appears
                if example_number == "1":
                    if first_example_seen:
                        chapter_counter += 1
                    else:
                        first_example_seen = True

                current_example = example_label
                question = match.group(3).strip()
                solution = ""
                state = "question"
                continue

            if line.startswith("Solution"):
                state = "solution"
                continue

            if state == "question":
                question += " " + line
            elif state == "solution":
                solution += " " + line

    # Save last
    if current_example:
        output.append(f"Chapter {chapter_counter} - {current_example}")
        output.append("Question: " + question.strip())
        output.append("First 1000 chars of Solution:")
        output.append(solution[:1000])
        output.append("-" * 80)

    with open("m_11_kb/examples.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))


# =====================================================
# RUN ALL
# =====================================================

# extract_topics_full_book()
# extract_examples_auto_chapter()
extract_information_text()
print("✅ Maths 11 full book parsing complete.")
