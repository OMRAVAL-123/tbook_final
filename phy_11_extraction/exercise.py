import fitz
import re
from tqdm import tqdm

PDF_PATH = "dataset/Physics-11.pdf"
OUTPUT_FILE = "p_11_kb/exercises.txt"

# From inspecting actual exercise pages:
# Question numbers (e.g. "2.14", "1.1") use:
#   font  = "Bookman-Demi" or "Bookman,Bold"
#   color = 44783  (teal — same as EXERCISES header and section labels)
#   size  = 9.0
# Body text uses:
#   font  = "Bookman-Light" or "Bookman"
#   color = 2301728  (dark)
#   size  = 9.0

Q_VALID_COLOR = 44783
Q_NUM_PATTERN = re.compile(r"^\d+\.\d{1,2}$")   # strict: "1.1", "2.14" only

# Gap threshold: vertical gap > this = paragraph break / end of question
GAP_THRESHOLD = 18.0  # pts

# All-caps section labels that signal start/end of sections
SECTION_LABELS = {
    "EXERCISES", "ADDITIONAL EXERCISES",
    "SUMMARY", "POINTS TO PONDER",
}


def extract_exercises(pdf_path):
    doc = fitz.open(pdf_path)
    exercises = []

    in_exercise   = False
    current_q_num = None
    current_q_text = []

    for page in tqdm(doc, desc="Processing Pages"):
        blocks = page.get_text("dict", sort=True)["blocks"]
        prev_bottom = None  # reset per page

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                line_top    = line["bbox"][1]
                line_bottom = line["bbox"][3]
                spans = line["spans"]
                if not spans:
                    continue

                line_text = " ".join(s["text"].strip() for s in spans if s["text"].strip())
                if not line_text:
                    continue

                first_span  = spans[0]
                first_color = first_span.get("color", -1)
                first_font  = first_span.get("font", "")
                first_size  = first_span.get("size", 0)
                first_text  = first_span["text"].strip()

                # ── Section label detection ──────────────────────────────────
                # All section labels (EXERCISES, SUMMARY, etc.) are teal (44783),
                # Bookman-Demi/Bold, size 9, and are ALL-CAPS short strings.
                is_section_label = (
                    first_color == Q_VALID_COLOR
                    and ("Demi" in first_font or "Bold" in first_font)
                    and 8.5 <= first_size <= 9.5
                    and line_text.strip().upper() in SECTION_LABELS
                )

                if is_section_label:
                    label = line_text.strip().upper()
                    if label == "EXERCISES" or label == "ADDITIONAL EXERCISES":
                        # Start of exercise section
                        in_exercise = True
                        if current_q_num and current_q_text:
                            _save(exercises, current_q_num, current_q_text)
                            current_q_num  = None
                            current_q_text = []
                    else:
                        # SUMMARY or POINTS TO PONDER = end of exercises
                        if in_exercise:
                            in_exercise = False
                            if current_q_num and current_q_text:
                                _save(exercises, current_q_num, current_q_text)
                                current_q_num  = None
                                current_q_text = []
                    prev_bottom = line_bottom
                    continue

                if not in_exercise:
                    prev_bottom = line_bottom
                    continue

                # ── Double-newline / gap detection ───────────────────────────
                if prev_bottom is not None:
                    gap = line_top - prev_bottom
                    if gap > GAP_THRESHOLD and current_q_num:
                        _save(exercises, current_q_num, current_q_text)
                        current_q_num  = None
                        current_q_text = []

                prev_bottom = line_bottom

                # ── Noise filter ─────────────────────────────────────────────
                if re.match(r"^\d+$", line_text):        # standalone page numbers
                    continue
                if line_text.startswith("Reprint"):      # "Reprint 2025-26"
                    continue
                if line_text.strip().upper() == "PHYSICS":
                    continue

                # ── Question number detection ────────────────────────────────
                # Q-numbers: Bookman-Demi/Bold, color=44783, size=9.0
                # The first span IS the number (e.g. "2.14"), rest is body text
                is_q_start = (
                    Q_NUM_PATTERN.match(first_text)
                    and ("Demi" in first_font or "Bold" in first_font)
                    and first_color == Q_VALID_COLOR
                    and 8.5 <= first_size <= 9.5
                )

                if is_q_start:
                    if current_q_num and current_q_text:
                        _save(exercises, current_q_num, current_q_text)

                    current_q_num  = first_text
                    current_q_text = []

                    # Rest of the line (body text after the number)
                    rest = " ".join(s["text"].strip() for s in spans[1:] if s["text"].strip())
                    if rest:
                        current_q_text.append(rest)

                elif current_q_num:
                    current_q_text.append(line_text)

    # EOF: save last question (max 500 chars)
    if current_q_num and current_q_text:
        _save(exercises, current_q_num, current_q_text, is_last=True)

    return exercises


def _save(exercises, q_num, q_text_list, is_last=False):
    text = " ".join(q_text_list).strip()
    text = re.sub(r"\s+", " ", text)
    if is_last and len(text) > 500:
        text = text[:500] + " ..."
    if text:
        exercises.append((q_num, text))


# ── Run ──────────────────────────────────────────────────────────────────────
extracted = extract_exercises(PDF_PATH)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for q_num, q_text in extracted:
        f.write(f"Question {q_num}\n{q_text}\n\n")

print(f"Done. Extracted {len(extracted)} questions → {OUTPUT_FILE}")
