
import fitz
import re
from tqdm import tqdm
import os

# Physics 11 Examples:
# - "Example X.Y" → Font: Bookman,Bold, Size: 10.0, Color: 44783
# - "Answer"      → Font: Bookman,Bold, Size: 10.0, Color: 44783
# - Body text     → Various, but we collect everything between headers.

def extract_examples_from_pdf(pdf_path, output_txt="p_11_kb/eg.txt"):
    print(f"Opening {pdf_path}...")
    try:
        pdf = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    examples = []
    current_example = None
    current_section = None
    
    # We'll use a slightly fuzzy float comparison for font size
    target_size = 10.0
    target_color = 44783
    target_font_substr = "Bookman"

    example_pattern = re.compile(r"^Example\s+\d+\.\d+")
    
    # Sometimes "Answer" might be followed by text on the same line or just be "Answer"
    # The user example showed "Answer Let us divide..." which implies it might differ or be on next line.
    # However, my previous probe showed "Answer" as a standalone span.
    # I will look for "Answer" as a standalone span or at start of span with the specific style.

    for page in tqdm(pdf, desc="Processing Pages"):
        text_dict = page.get_text("dict")
        blocks = text_dict["blocks"]

        # Column-wise sorting to handle double columns if any, though standard textbooks are usually single or complex.
        # Physics 11 is likely single or double. Let's stick to standard sorting or top-down.
        # But sorting by vertical position then horizontal is safer for reading flow if it's single column.
        # If double column, we need column sorting.
        # Let's try to assume text flow is reasonable with basic sorting or fitz's default order?
        # Fitz default order in "dict" is usually block order. 
        # But let's apply the sort key from chem_12 just in case: (col, y0).
        
        def get_block_sort_key(b):
            x0 = b["bbox"][0]
            y0 = b["bbox"][1]
            # Simple column detection: headers usually span, but content might be 2 cols.
            # If x0 < page_width/2 it's col 1, else col 2.
            # Page width is usually ~600.
            col = int(x0 / 300) 
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
                    
                    # Check for Example Header
                    is_example_header = (
                        target_font_substr in font and
                        abs(size - target_size) < 0.5 and
                        color == target_color and
                        example_pattern.match(text)
                    )

                    if is_example_header:
                        # Ensure we save the previous example
                        if current_example:
                            examples.append(current_example)
                        
                        current_example = {
                            "id": text, # captures "Example 1.1"
                            "question": "",
                            "solution": ""
                        }
                        current_section = "question"
                        continue

                    # Check for Answer Header
                    # Based on user input: "Answer Let us..." might happen? 
                    # But my probe found "Answer" as a separate span.
                    # I will check if it matches "Answer" exactly or starts with "Answer" and has the style.
                    is_answer_header = (
                        target_font_substr in font and
                        abs(size - target_size) < 0.5 and
                        color == target_color and
                        (text == "Answer" or text.startswith("Answer"))
                    )

                    if is_answer_header and current_example:
                        current_section = "solution"
                        # If the span content is just "Answer", we continue.
                        # If it is "Answer Let us...", we should grab the "Let us..." part.
                        # My probe showed "Answer" is separate usually.
                        if text == "Answer":
                            continue
                        else:
                            # It has content after Answer?
                            # Example: "Answer The distance..."
                            # We should append the rest to solution.
                            content = text[len("Answer"):].strip()
                            if content:
                                current_example["solution"] += content + " "
                        continue

                    # Logic to capture content
                    if current_example and current_section:
                        # Filter out noise?
                        # Page numbers, headers often have different colors or positions.
                        # For now, let's just append.
                        
                        if current_section == "question":
                            current_example["question"] += text + " "
                        elif current_section == "solution":
                            current_example["solution"] += text + " "

    # Append the last one
    if current_example:
        examples.append(current_example)

    # Write output
    os.makedirs(os.path.dirname(output_txt), exist_ok=True)
    
    with open(output_txt, "w", encoding="utf-8") as f:
        for ex in examples:
            question = re.sub(r'\s+', ' ', ex["question"]).strip()
            solution = re.sub(r'\s+', ' ', ex["solution"]).strip()
            
            # User asked for "first 1000 chars of soluton"
            solution_snippet = solution[:1000]

            f.write(f"{ex['id']}\n")
            f.write(f"Question: {question}\n")
            f.write("First 1000 chars of Solution:\n")
            f.write(f"{solution_snippet}\n")
            f.write("-" * 80 + "\n\n")

    print(f"✅ Done. Extracted {len(examples)} examples. Saved to {output_txt}")

if __name__ == "__main__":
    pdf_source = r"d:\tbook_final\dataset\Physics-11.pdf"
    output_file = r"d:\tbook_final\p_11_kb\eg.txt"
    extract_examples_from_pdf(pdf_source, output_file)
