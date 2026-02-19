import fitz
import re
from tqdm import tqdm

# Chemistry 12 Examples:
# - "Example X.Y" → Font: BallroomTango, Size: 13.0, Color: 44783
# - "Solution"    → Font: BallroomTango, Size: 13.0, Color: 44783
# - Body text     → Font: Bookman-Light, Size: 10.5, Color: 2301728
# Note: BallroomTango text repeats 5x (shadow effect) — deduplicate by tracking last seen

def extract_examples_from_pdf(pdf_path, output_txt="c_12_kb/examples.txt"):
    pdf = fitz.open(pdf_path)
    examples = []
    current_example = None
    current_section = None
    last_seen_label = None  # to deduplicate BallroomTango repeats

    example_pattern = re.compile(r"^Example\s+\d+\.\d+$")

    for page in tqdm(pdf, desc="Processing Pages"):
        text_dict = page.get_text("dict")
        blocks = text_dict["blocks"]

        # Column-wise sorting
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
                    font = span["font"]
                    size = span["size"]
                    color = span["color"]

                    if not text:
                        continue

                    # Detect Example header: BallroomTango, size~13, color=44783
                    if ("BallroomTango" in font
                            and abs(size - 13.0) < 0.5
                            and color == 44783
                            and example_pattern.match(text)):
                        if text == last_seen_label:
                            continue  # skip duplicate shadow
                        last_seen_label = text

                        if current_example:
                            examples.append(current_example)

                        current_example = {
                            "id": text,
                            "question": "",
                            "solution": ""
                        }
                        current_section = "question"
                        continue

                    # Detect Solution header: BallroomTango, size~13, color=44783
                    if ("BallroomTango" in font
                            and abs(size - 13.0) < 0.5
                            and color == 44783
                            and text == "Solution"):
                        if text == last_seen_label:
                            continue
                        last_seen_label = text
                        current_section = "solution"
                        continue

                    # Reset last_seen_label for non-BallroomTango text
                    if "BallroomTango" not in font:
                        last_seen_label = None

                    # Capture body text
                    if current_example and current_section:
                        # Skip noise: page numbers, running headers
                        if re.match(r"^Reprint \d{4}-\d{2}$", text):
                            continue
                        if color == 7171953:  # running header color
                            continue

                        if current_section == "question":
                            current_example["question"] += text + " "
                        elif current_section == "solution":
                            current_example["solution"] += text + " "

    if current_example:
        examples.append(current_example)

    # Write output
    import os
    os.makedirs("c_12_kb", exist_ok=True)
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

    print(f"✅ Done. Extracted {len(examples)} examples. Saved to {output_txt}")


if __name__ == "__main__":
    extract_examples_from_pdf("Chemistry-12.pdf")
