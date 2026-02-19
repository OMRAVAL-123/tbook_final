import fitz
import re
from tqdm import tqdm

PDF_PATH = "dataset/Physics-11.pdf"
OUTPUT_FILE = "p_11_kb/topics.txt"

# Strict regex: 1-2 digits per part (e.g., 1.1, 10.5, 12.4.1). 
section_pattern = re.compile(r"^(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\s*(.*)", re.IGNORECASE)

def is_blueish(color):
    """
    Check if color is the specific blue used for headers (#00aeef, #00bdf2).
    Logic: High Blue, High Green (Cyan-like), Low Red.
    """
    r = (color >> 16) & 0xFF
    g = (color >> 8) & 0xFF
    b = color & 0xFF
    # Heuristic for the specific blue used in this PDF
    return (b > 100) and (g > 100) and (r < 50)

def extract_topics(pdf_path):
    doc = fitz.open(pdf_path)
    # Store tuples: (sec_num_tuple, sec_num_str, title)
    extracted_entries = []
    seen_sections = set()
    
    for page in tqdm(doc, desc="Processing Pages"):
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue
            
            lines = block["lines"]
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Get line details
                line_parts = []
                max_size = 0
                has_blue = False
                
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        line_parts.append(text)
                        max_size = max(max_size, span["size"])
                        if is_blueish(span["color"]):
                            has_blue = True
                
                full_line = " ".join(line_parts).strip()
                if not full_line:
                    i += 1
                    continue
                
                # Filter by size
                if max_size < 9.7:
                    i += 1
                    continue

                # Check pattern
                match_sec = section_pattern.match(full_line)
                if match_sec:
                    sec_num = match_sec.group(1)
                    sec_title = match_sec.group(2).strip()
                    
                    # Merge Logic
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        n_parts = []
                        n_max_size = 0
                        n_has_blue = False
                        
                        for span in next_line["spans"]:
                            t = span["text"].strip()
                            if t:
                                n_parts.append(t)
                                n_max_size = max(n_max_size, span["size"])
                                if is_blueish(span["color"]):
                                    n_has_blue = True
                        
                        n_full_line = " ".join(n_parts).strip()
                        if not n_full_line:
                            j += 1
                            continue 
                            
                        # Break if size drops or new section starts
                        if n_max_size < 9.7: 
                            break
                        if section_pattern.match(n_full_line):
                            break
                        
                        sec_title += " " + n_full_line
                        if n_has_blue:
                            has_blue = True
                        j += 1
                    
                    i = j 
                    sec_title = sec_title.strip()

                    # Color Filter
                    if not has_blue:
                        continue

                    # Text Filters
                    if len(sec_title) < 2: continue
                    if sec_title.lower().startswith(("summary", "exercise", "points to ponder")): continue
                    if not sec_title[0].isupper(): continue
                    if len(sec_title) > 200: continue
                    if sum(c.isalpha() for c in sec_title) < 3: continue
                    
                    # Deduplication
                    if sec_num in seen_sections:
                        continue
                    
                    # Store for sorting
                    # Check chapter validity (1-15)
                    try:
                        parts = [int(x) for x in sec_num.split(".")]
                        chap = parts[0]
                        if 1 <= chap <= 15:
                            extracted_entries.append((tuple(parts), sec_num, sec_title))
                            seen_sections.add(sec_num)
                    except ValueError:
                        pass
                    
                    continue
                
                i += 1

    return extracted_entries

if __name__ == "__main__":
    entries = extract_topics(PDF_PATH)
    
    # Sort entries numerically
    entries.sort(key=lambda x: x[0])
    
    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        current_chapter = None
        for _, sec_num, sec_title in entries:
            chap = int(sec_num.split(".")[0])
            
            # Insert Chapter Header
            if chap != current_chapter:
                f.write(f"\nChapter {chap}\n")
                current_chapter = chap
                
            level = sec_num.count(".")
            indent = "    " * (level - 1)
            f.write(f"{indent}{sec_num} {sec_title}\n")

    print(f"Done. Extracted {len(entries)} topics.")
