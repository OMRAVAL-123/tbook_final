import fitz
import re
from tqdm import tqdm

pdf_path = "dataset/Physics-12.pdf"
doc = fitz.open(pdf_path)

output_lines = []

current_chapter_number = ""
current_chapter_title = ""

def clean_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(\d+\.\d+)\s+\1", r"\1", text)  # remove duplicated numbering
    return text

for page in tqdm(doc, desc="Extracting Full Book Structure"):
    text_dict = page.get_text("dict")

    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            full_text = ""
            sizes = []

            for span in line["spans"]:
                full_text += span["text"]
                sizes.append(round(span["size"], 2))

            full_text = clean_text(full_text)

            if not full_text:
                continue

            # ===== Detect Chapter Number (e.g., Chapter One) =====
            if 30.0 in sizes and "Chapter" in full_text:
                current_chapter_number = full_text.strip()
                continue

            # ===== Detect Chapter Title =====
            if 48.0 in sizes:
                current_chapter_title = full_text.upper()
                output_lines.append(f"\nUnit: {current_chapter_number} - {current_chapter_title}")
                continue

            # ===== Detect Section (x.y) =====
            if 16.0 in sizes:
                if re.match(r"^\d+\.\d+\s", full_text):
                    output_lines.append(full_text)
                continue

            # ===== Detect Subsection (x.y.z) =====
            if 12.0 in sizes:
                if re.match(r"^\d+\.\d+\.\d+", full_text):
                    output_lines.append("    " + full_text)
                continue

# Save Output
with open("p_12_kb/topics.txt", "w", encoding="utf-8") as f:
    for line in output_lines:
        f.write(line + "\n")

print("✅ Full book structure saved to p_12_kb/topics.txt")
