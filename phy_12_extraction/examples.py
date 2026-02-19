import fitz
import re
from tqdm import tqdm

pdf_path = "dataset/Physics-12.pdf"
doc = fitz.open(pdf_path)

output_lines = []

current_example = None
question_text = ""
solution_text = ""

state = "idle"  # idle | question | solution

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

for page in tqdm(doc, desc="Extracting Examples Properly"):
    text = page.get_text()
    lines = text.split("\n")

    for line in lines:
        line = clean(line)
        if not line:
            continue

        # ===== Detect New Example =====
        example_match = re.match(r"(Example\s+\d+\.\d+)(.*)", line)

        if example_match:
            # Save previous example
            if current_example:
                output_lines.append(current_example)
                output_lines.append(f"Question: {question_text.strip()}")
                output_lines.append("First 1000 chars of Solution:")
                output_lines.append(solution_text[:1000])
                output_lines.append("-" * 80)
                output_lines.append("")

            current_example = example_match.group(1)
            question_text = example_match.group(2).strip()
            solution_text = ""
            state = "question"
            continue

        # ===== Detect Solution =====
        if line.startswith("Solution"):
            state = "solution"
            continue

        # ===== Collect Question =====
        if state == "question":
            question_text += " " + line

        # ===== Collect Solution =====
        elif state == "solution":
            solution_text += " " + line

# Save last example
if current_example:
    output_lines.append(current_example)
    output_lines.append(f"Question: {question_text.strip()}")
    output_lines.append("First 1000 chars of Solution:")
    output_lines.append(solution_text[:1000])
    output_lines.append("-" * 80)

# Write to file
with open("physics12_examples_clean.txt", "w", encoding="utf-8") as f:
    for line in output_lines:
        f.write(line + "\n")

print("✅ Clean example extraction complete.")
