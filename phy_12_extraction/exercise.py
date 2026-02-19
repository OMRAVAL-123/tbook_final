import fitz
import re
from tqdm import tqdm

pdf_path = "dataset/Physics-12.pdf"
doc = fitz.open(pdf_path)

output_lines = []

current_question = None
question_text = ""

def is_black(color):
    r = (color >> 16) & 255
    g = (color >> 8) & 255
    b = color & 255
    return (r, g, b) == (35, 31, 32)

for page in tqdm(doc, desc="Extracting Exercises (CSS-based)"):
    text_dict = page.get_text("dict")

    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue

        for line in block["lines"]:

            line_text = ""
            font_names = []
            colors = []

            for span in line["spans"]:
                line_text += span["text"]
                font_names.append(span["font"])
                colors.append(span["color"])

            line_text = re.sub(r"\s+", " ", line_text).strip()
            if not line_text:
                continue

            # ===== Detect Question Start via CSS =====
            if (
                any("Demi" in f or "Bold" in f for f in font_names)
                and any(is_black(c) for c in colors)
                and re.match(r"^\d+\.\d+", line_text)
            ):
                # Save previous question
                if current_question:
                    output_lines.append(f"Question {current_question}")
                    output_lines.append(question_text[:1000])
                    output_lines.append("")

                current_question = re.match(r"^(\d+\.\d+)", line_text).group(1)
                question_text = line_text[len(current_question):].strip()
                continue

            # ===== Append body text =====
            if current_question:
                question_text += " " + line_text

                if len(question_text) >= 1000:
                    output_lines.append(f"Question {current_question}")
                    output_lines.append(question_text[:1000])
                    output_lines.append("")

                    current_question = None
                    question_text = ""

# Save last question
if current_question:
    output_lines.append(f"Question {current_question}")
    output_lines.append(question_text[:1000])
    output_lines.append("")

with open("p_12_kb/exercises.txt", "w", encoding="utf-8") as f:
    for line in output_lines:
        f.write(line + "\n")

print("✅ Exercises extracted using CSS styling.")
