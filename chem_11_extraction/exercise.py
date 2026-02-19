import fitz
import re

def extract_exercises(pdf_path, output_txt="c_11_kb/exercise.txt"):
    pdf = fitz.open(pdf_path)
    
    # Map: exercise_start_page (1-indexed) -> chapter_name
    # Detected from running headers near exercise sections
    exercise_chapters = {
        25:  "Some Basic Concepts of Chemistry",
        69:  "Structure of Atom",
        96:  "Classification of Elements and Periodicity in Properties",
        133: "Chemical Bonding And Molecular Structure",
        165: "Thermodynamics",
        208: "Equilibrium",
        232: "Redox Reactions",
        272: "Organic Chemistry – Some Basic Principles and Techniques",
        306: "Hydrocarbons",
    }
    
    # Sort exercise start pages
    exercise_start_pages = sorted(exercise_chapters.keys())
    
    # Build list of (start_page_0indexed, end_page_0indexed, chapter_name)
    # End page is the page before the next exercise section starts
    sections = []
    for i, sp in enumerate(exercise_start_pages):
        chapter = exercise_chapters[sp]
        chapter_num = i + 1  # chapters are numbered 1-9 in order
        start_0 = sp - 1  # convert to 0-indexed
        if i + 1 < len(exercise_start_pages):
            end_0 = exercise_start_pages[i + 1] - 2  # page before next section
        else:
            end_0 = len(pdf) - 1
        sections.append((start_0, end_0, chapter, chapter_num))
    
    # Pattern: question number like "1.1", "2.10", "9.40" etc.
    # Must be: single digit chapter (1-9), dot, 1-2 digit question number (1-99)
    q_num_pattern = re.compile(r"^[1-9]\.\d{1,2}$")
    
    # Noise patterns to skip
    noise_patterns = [
        re.compile(r"^Reprint \d{4}-\d{2}$"),
        re.compile(r"^\d+$"),  # standalone page numbers
    ]
    
    all_exercises = []  # list of (chapter_name, q_number, q_text)
    
    for start_0, end_0, chapter, chapter_num in sections:
        print(f"Processing: {chapter} (pages {start_0+1}-{end_0+1})")
        
        in_exercises = False
        current_q_num = None
        current_q_text = []
        # Exercise numbers must start with this chapter's number
        valid_q_prefix = f"{chapter_num}."
        
        for page_num in range(start_0, end_0 + 1):
            page = pdf[page_num]
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    # First pass: collect all non-empty spans on this line
                    spans_on_line = []
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        spans_on_line.append((text, span["size"], span["color"], span["flags"]))
                    
                    if not spans_on_line:
                        continue
                    
                    # Check if we're still looking for the EXERCISES header
                    if not in_exercises:
                        for text, size, color, flags in spans_on_line:
                            if "EXERCISE" in text.upper() and color == 2301728 and size >= 9.0:
                                in_exercises = True
                                break
                        continue
                    
                    # Skip lines that are purely running headers (size=8.0, color=2301728)
                    if all(size == 8.0 and color == 2301728 for _, size, color, _ in spans_on_line):
                        continue
                    
                    # Skip lines that are purely noise
                    def is_noise(text):
                        for np in noise_patterns:
                            if np.match(text):
                                return True
                        return False
                    
                    if all(is_noise(t) for t, _, _, _ in spans_on_line):
                        continue
                    
                    # Check if this line is SOLELY an exercise number
                    # (exactly one span, matching X.Y pattern, correct size/color,
                    #  AND the number prefix matches the current chapter number)
                    if len(spans_on_line) == 1:
                        text, size, color, flags = spans_on_line[0]
                        if (q_num_pattern.match(text) and text.startswith(valid_q_prefix)
                                and abs(size - 9.5) < 0.5 and color == 2301728):
                            # Save previous question
                            if current_q_num is not None:
                                q_text = " ".join(current_q_text).strip()
                                q_text = re.sub(r'\s+', ' ', q_text)
                                if q_text:
                                    all_exercises.append((chapter, current_q_num, q_text))
                            current_q_num = text
                            current_q_text = []
                            continue
                    
                    # Detect chapter-intro "Unit X" headers — stop accumulating if seen
                    # These appear as large colored text like "Unit 2 structure of atom"
                    is_chapter_intro = any(
                        re.match(r'^Unit\s+\d+', text, re.IGNORECASE) and color == 2301728 and size >= 10.0
                        for text, size, color, _ in spans_on_line
                    )
                    if is_chapter_intro and current_q_num is not None:
                        # Save current question and stop processing this section
                        q_text = " ".join(current_q_text).strip()
                        q_text = re.sub(r'\s+', ' ', q_text)
                        if q_text:
                            all_exercises.append((chapter, current_q_num, q_text))
                        current_q_num = None
                        current_q_text = []
                        in_exercises = False  # stop processing further
                        break
                    
                    # Otherwise accumulate as question body text
                    if current_q_num is not None:
                        # Guard: don't accumulate beyond a reasonable question length
                        current_len = sum(len(t) for t in current_q_text)
                        if current_len > 1000:
                            continue
                        line_parts = []
                        for text, size, color, flags in spans_on_line:
                            # Skip running header spans within a mixed line
                            if size == 8.0 and color == 2301728:
                                continue
                            if is_noise(text):
                                continue
                            line_parts.append(text)
                        if line_parts:
                            joined = " ".join(line_parts)
                            # Stop if this line looks like a chapter-intro sentinel
                            chapter_intro_sentinels = [
                                r'After studying this unit',
                                r'Unit \d+ ',
                            ]
                            sentinel_match = None
                            for pat in chapter_intro_sentinels:
                                m = re.search(pat, joined, re.IGNORECASE)
                                if m:
                                    sentinel_match = m
                                    break
                            if sentinel_match:
                                # Keep only the text before the sentinel
                                pre_sentinel = joined[:sentinel_match.start()].strip()
                                if pre_sentinel:
                                    current_q_text.append(pre_sentinel)
                                # Save current question and stop
                                q_text = " ".join(current_q_text).strip()
                                q_text = re.sub(r'\s+', ' ', q_text)
                                if q_text:
                                    all_exercises.append((chapter, current_q_num, q_text))
                                current_q_num = None
                                current_q_text = []
                                in_exercises = False
                                break
                            current_q_text.append(joined)
        
        # Save last question of this section
        if current_q_num is not None:
            q_text = " ".join(current_q_text).strip()
            q_text = re.sub(r'\s+', ' ', q_text)
            if q_text:
                all_exercises.append((chapter, current_q_num, q_text))
            current_q_num = None
            current_q_text = []
    
    # Write output
    with open(output_txt, "w", encoding="utf-8") as f:
        current_chapter = None
        for chapter, q_num, q_text in all_exercises:
            if chapter != current_chapter:
                if current_chapter is not None:
                    f.write("\n")
                f.write(f"{chapter}\n")
                f.write("=" * len(chapter) + "\n\n")
                current_chapter = chapter
            
            f.write(f"Exercise {q_num}\n")
            f.write(q_text + "\n\n")
    
    print(f"\n✅ Done! Extracted {len(all_exercises)} exercises.")
    print(f"   Saved to: {output_txt}")


if __name__ == "__main__":
    extract_exercises("c_11.pdf")
