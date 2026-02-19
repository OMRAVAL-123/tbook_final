import fitz
import re
import os

PDF_PATH = "Chemistry-12.pdf"
TXT_TOPICS = "c_12_kb/topics.txt"

# ============================================================
# Chemistry 12 — Topics / Section Headings Extractor
# ============================================================
#
# CSS patterns (verified from css.txt + debug_fonts.py):
#
# MAIN SECTION headings (e.g. "1.1 Types of Solutions"):
#   Font: BallroomTango, size~14.0
#   Color: 2301728 for chapters 1-5, OR 7171953 for chapters 6-10
#   Text repeats 5x (shadow effect) — deduplicate!
#   Number and title may be in same span OR separate spans.
#
# SUB-SECTION headings (e.g. "1.3.1 Solubility of a Solid in a Liquid"):
#   Number: Bookman-Demi, size~10.5, color=7171953 (grey)
#   Title:  Bookman-Demi, size~10.5, color=2301728 (dark)
#
# CHAPTER TITLE PAGES: rendered as images — not extractable as text.
#   Chapter start pages are hardcoded below.
# ============================================================

# Hardcoded chapter data (page = 1-indexed, verified by debug_fonts.py)
CHAPTERS = [
    {"num": 1,  "page": 1,   "name": "Solutions"},
    {"num": 2,  "page": 32,  "name": "Electrochemistry"},
    {"num": 3,  "page": 62,  "name": "Chemical Kinetics"},
    {"num": 4,  "page": 90,  "name": "d- and f-Block Elements"},
    {"num": 5,  "page": 118, "name": "Coordination Compounds"},
    {"num": 6,  "page": 142, "name": "Haloalkanes and Haloarenes"},
    {"num": 7,  "page": 176, "name": "Alcohols, Phenols and Ethers"},
    {"num": 8,  "page": 210, "name": "Aldehydes, Ketones and Carboxylic Acids"},
    {"num": 9,  "page": 241, "name": "Amines"},
    {"num": 10, "page": 263, "name": "Biomolecules"},
]

# BallroomTango section heading colors
SECTION_COLORS = {2301728, 7171953}

SIZE_TOL = 1.0


def get_chapter_for_page(page_1indexed):
    """Return chapter dict for a given 1-indexed page number."""
    current = None
    for ch in CHAPTERS:
        if ch["page"] <= page_1indexed:
            current = ch
        else:
            break
    return current


def is_ballroom_section(font, size, color):
    return ("BallroomTango" in font
            and abs(size - 14.0) < SIZE_TOL
            and color in SECTION_COLORS)


def is_subsec_num(font, size, color, text):
    """Sub-section number: Bookman-Demi, size~10.5, color=7171953, matches X.Y.Z"""
    return ("Bookman-Demi" in font
            and abs(size - 10.5) < 0.5
            and color == 7171953
            and re.match(r"^\d+\.\d+\.\d+", text))


def is_subsec_title(font, size, color):
    """Sub-section title: Bookman-Demi, size~10.5, color=2301728"""
    return ("Bookman-Demi" in font
            and abs(size - 10.5) < 0.5
            and color == 2301728)


def extract_sections_from_page(page):
    """
    Extract section headings from a page.
    Returns list of ("main", "X.Y", "Title") or ("sub", "X.Y.Z", "Title")
    """
    results = []
    blocks = page.get_text("dict")["blocks"]

    for block in blocks:
        if "lines" not in block:
            continue

        lines_data = []
        for line in block["lines"]:
            spans = []
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue
                spans.append((text, span["font"], span["size"], span["color"]))
            if spans:
                lines_data.append(spans)

        i = 0
        while i < len(lines_data):
            spans = lines_data[i]

            # ---- MAIN SECTION: all spans are BallroomTango size~14 ----
            if all(is_ballroom_section(f, s, c) for _, f, s, c in spans):
                # Collect all consecutive BallroomTango lines
                ballroom_lines = []
                while i < len(lines_data) and all(
                    is_ballroom_section(f, s, c) for _, f, s, c in lines_data[i]
                ):
                    ballroom_lines.append(lines_data[i])
                    i += 1

                # Collect unique text tokens (deduplicate 5x shadow)
                unique_texts = []
                seen = set()
                for line_spans in ballroom_lines:
                    for text, _, _, _ in line_spans:
                        if text not in seen:
                            seen.add(text)
                            unique_texts.append(text)

                if not unique_texts:
                    continue

                # The first token may be "X.Y" alone, or "X.Y Title words"
                # Join all unique texts and parse
                full = " ".join(unique_texts).strip()

                # Match section number at start: X.Y or X.Y.Z
                m = re.match(r"^(\d+\.\d+(?:\.\d+)?)\s*(.*)", full)
                if m:
                    sec_num = m.group(1)
                    title = m.group(2).strip()
                    # Clean repeated words (e.g. "Factors Influencing Factors Influencing")
                    title = _dedup_phrase(title)
                    results.append(("main", sec_num, title))
                continue

            # ---- SUB-SECTION: Bookman-Demi color=7171953 number ----
            sub_num = None
            for t, f, s, c in spans:
                if is_subsec_num(f, s, c, t):
                    sub_num = t
                    break

            if sub_num:
                title_parts = []
                # Title on same line
                for t, f, s, c in spans:
                    if is_subsec_title(f, s, c):
                        title_parts.append(t)
                # Title on following lines
                j = i + 1
                while j < len(lines_data):
                    next_spans = lines_data[j]
                    if any(is_subsec_num(f, s, c, t) for t, f, s, c in next_spans):
                        break
                    if any(is_ballroom_section(f, s, c) for _, f, s, c in next_spans):
                        break
                    if all(is_subsec_title(f, s, c) for _, f, s, c in next_spans):
                        for t, _, _, _ in next_spans:
                            title_parts.append(t)
                        j += 1
                    else:
                        break

                title = " ".join(title_parts).strip()
                if title:
                    results.append(("sub", sub_num, title))

            i += 1

    return results


def _dedup_phrase(text):
    """Remove repeated halves: 'Foo Bar Foo Bar' → 'Foo Bar'"""
    if not text:
        return text
    words = text.split()
    n = len(words)
    for half in range(n // 2, 0, -1):
        if words[:half] == words[half:half*2]:
            return " ".join(words[:half])
    return text


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    doc = fitz.open(PDF_PATH)
    print(f"Loaded {PDF_PATH} ({len(doc)} pages)")
    print(f"Processing {len(CHAPTERS)} chapters...")

    # Collect sections per chapter
    chapter_sections = {ch["num"]: [] for ch in CHAPTERS}
    seen_keys = set()

    for page_num in range(len(doc)):
        page_1 = page_num + 1
        ch = get_chapter_for_page(page_1)
        if ch is None:
            continue

        page = doc[page_num]
        sections = extract_sections_from_page(page)

        for sec_type, sec_num, title in sections:
            # Validate: section number must belong to this chapter
            sec_ch = int(sec_num.split(".")[0])
            if sec_ch != ch["num"]:
                continue

            key = (ch["num"], sec_num)
            if key not in seen_keys:
                seen_keys.add(key)
                chapter_sections[ch["num"]].append((sec_type, sec_num, title))

    # Sort sections within each chapter
    def sec_sort_key(item):
        try:
            return [int(p) for p in item[1].split(".")]
        except ValueError:
            return [0]

    for ch_num in chapter_sections:
        chapter_sections[ch_num].sort(key=sec_sort_key)

    # Write output
    os.makedirs("c_12_kb", exist_ok=True)
    with open(TXT_TOPICS, "w", encoding="utf-8") as f:
        for ch in CHAPTERS:
            f.write(f"\nUnit {ch['num']}: {ch['name'].upper()}\n")

            sections = chapter_sections.get(ch["num"], [])
            if not sections:
                f.write("  [No sections extracted]\n")
                print(f"  Chapter {ch['num']}: NO sections found!")
                continue

            for sec_type, sec_num, title in sections:
                depth = sec_num.count(".")
                indent = "    " * (depth - 1)
                f.write(f"{indent}{sec_num} {title}\n")

            print(f"  Chapter {ch['num']} ({ch['name']}): {len(sections)} sections")

    print(f"\nCreated {TXT_TOPICS}")
    doc.close()
    print("Done.")
