import fitz
import re
import os

PDF_PATH = "c_11.pdf"
TXT_TOPICS = "c_11_kb/topics.txt"

UNIT_LABEL_SIZE = 16.0
TITLE_SIZE = 19.0
SIZE_TOLERANCE = 0.5


# ==========================================
# 1. CHAPTER SCANNING
# ==========================================

def scan_all_chapters(doc):
    chapters = []
    print("Scanning for chapters...")

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        large_spans = []
        for b in blocks:
            if "lines" not in b:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    size = round(span["size"], 1)
                    if size >= 15.0:
                        large_spans.append({
                            "text": span["text"].strip(),
                            "size": size
                        })

        unit_label = None
        for sp in large_spans:
            match = re.match(r"^(Unit\s*\d+)", sp["text"], re.IGNORECASE)
            if match and abs(sp["size"] - UNIT_LABEL_SIZE) < SIZE_TOLERANCE:
                unit_label = match.group(1).strip()
                break

        if unit_label:
            title_parts = []
            for sp in large_spans:
                if abs(sp["size"] - TITLE_SIZE) < SIZE_TOLERANCE:
                    title_parts.append(sp["text"])

            title = " ".join(title_parts).strip()

            if title and not any(c['unit'] == unit_label for c in chapters):
                chapters.append({
                    "page": page_num,
                    "unit": unit_label,
                    "title": title
                })
                print(f"  Found {unit_label}: {title} (Page {page_num+1})")

    return sorted(chapters, key=lambda x: x["page"])


def get_current_chapter(chapters, page_num):
    current = None
    for ch in chapters:
        if ch["page"] <= page_num:
            current = f"{ch['unit']}: {ch['title']}"
        else:
            break
    return current if current else None


# ==========================================
# 2. SECTION EXTRACTION
# ==========================================

def commit_title(buffer_text, chapter, output_list):
    full_text = re.sub(r'\s+', ' ', buffer_text).strip()
    match = re.match(r"^(\d+(?:\.\d+)*)\.?\s*(.*)", full_text)
    if match:
        sec_num = match.group(1)
        title = match.group(2).strip()
        if '.' in sec_num:
            output_list.append((chapter, sec_num, title))


def extract_titles(blocks, chapter, output_list, buffer_state):
    curr_buf = buffer_state.get("buffer", "")

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if not text:
                    continue

                is_heading = (span["color"] == 44783 and 10.0 < span["size"] < 11.0)

                if is_heading:
                    if re.match(r"^\d+\.\d+", text):
                        if curr_buf.strip():
                            commit_title(curr_buf, chapter, output_list)
                            curr_buf = ""
                    curr_buf += span["text"] + " "
                else:
                    if curr_buf.strip():
                        commit_title(curr_buf, chapter, output_list)
                        curr_buf = ""

    buffer_state["buffer"] = curr_buf


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    if os.path.exists(TXT_TOPICS):
        os.remove(TXT_TOPICS)

    doc = fitz.open(PDF_PATH)
    print(f"Loaded {PDF_PATH} ({len(doc)} pages)")

    chapters_map = scan_all_chapters(doc)

    print("Extracting topics...")

    all_titles = []
    title_state = {"buffer": ""}
    current_chapter_name = None

    for page_num in range(len(doc)):
        page_chapter = get_current_chapter(chapters_map, page_num)

        if page_chapter != current_chapter_name:
            if title_state["buffer"].strip():
                commit_title(title_state["buffer"], current_chapter_name, all_titles)
                title_state["buffer"] = ""
            current_chapter_name = page_chapter

        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        extract_titles(blocks, current_chapter_name, all_titles, title_state)

    if title_state["buffer"].strip():
        commit_title(title_state["buffer"], current_chapter_name, all_titles)

    # Remove duplicates
    seen = set()
    unique_titles = []
    for t in all_titles:
        if (t[0], t[1]) not in seen:
            seen.add((t[0], t[1]))
            unique_titles.append(t)

    # Sorting
    ch_index = {c['unit']+": "+c['title']: i for i, c in enumerate(chapters_map)}

    unique_titles.sort(
        key=lambda x: (
            ch_index.get(x[0], 999),
            [int(k) for k in x[1].split('.')]
        )
    )

    # Write formatted output
    with open(TXT_TOPICS, "w", encoding="utf-8") as f:
        last_ch = None
        for item in unique_titles:
            if item[0] != last_ch:
                f.write(f"\n{item[0]}\n")
                last_ch = item[0]

            indent = "    " * (item[1].count('.') - 1)
            f.write(f"{indent}{item[1]} {item[2]}\n")

    print(f"Created {TXT_TOPICS}")
    doc.close()
    print("Done.")
