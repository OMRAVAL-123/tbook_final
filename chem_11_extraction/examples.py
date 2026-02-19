import fitz
import re
from tqdm import tqdm

def extract_problems_from_pdf(pdf_path, output_txt="c_11_kb/problems.txt"):
    pdf = fitz.open(pdf_path)
    examples = []
    current_example = None
    current_section = None

    problem_pattern = re.compile(r"^Problem\s+\d+\.\d+")

    # 🔥 tqdm added here
    for page in tqdm(pdf, desc="Processing Pages"):
        text_dict = page.get_text("dict")
        blocks = text_dict["blocks"]

        # ---- Column-wise sorting ----
        def get_block_sort_key(b):
            x0 = b["bbox"][0]
            y0 = b["bbox"][1]
            col = int(x0 / 250)
            return (col, y0)

        blocks.sort(key=get_block_sort_key)

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    color = span["color"]

                    if not text:
                        continue

                    # Detect Problem
                    if color == 2301728 and problem_pattern.match(text):
                        if current_example:
                            examples.append(current_example)

                        current_example = {
                            "id": text,
                            "question": "",
                            "solution": ""
                        }
                        current_section = "question"
                        continue

                    # Detect Solution
                    if color == 2301728 and "Solution" in text:
                        current_section = "solution"
                        continue

                    # Capture text
                    if current_example and current_section:
                        if current_section == "question":
                            current_example["question"] += text + " "
                        elif current_section == "solution":
                            current_example["solution"] += text + " "

    if current_example:
        examples.append(current_example)

    # Write output
    with open(output_txt, "w", encoding="utf-8") as f:
        for ex in examples:
            question = re.sub(r'\s+', ' ', ex["question"]).strip()
            solution = re.sub(r'\s+', ' ', ex["solution"]).strip()
            solution_1000 = solution[:1000]

            f.write(f"{ex['id']}\n")
            f.write("Q: " + question + "\n")
            f.write("First 1000 chars of Solution:\n")
            f.write(solution_1000 + "\n")
            f.write("-" * 80 + "\n\n")

    print("✅ Done. Saved to problems_output.txt")


if __name__ == "__main__":
    extract_problems_from_pdf("c_11.pdf")
