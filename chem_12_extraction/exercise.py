import fitz
import re
import os

PDF_PATH = "Chemistry-12.pdf"
OUTPUT_FILE = "c_12_kb/questions.txt"

# Start pages of Exercises for selected chapters (1-indexed)
# Supplied by user: 284 260 237 204 171 138 115 85 59 27
EXERCISE_STARTS = sorted([284, 260, 237, 204, 171, 138, 115, 85, 59, 27])

def is_noise(text):
    if re.match(r'^Reprint', text, re.IGNORECASE): return True
    if text.strip() in ["Chemistry", "Solutions", "Electrochemistry", "Chemical Kinetics"]: return True
    # Page numbers often appear alone
    if re.match(r'^\d+$', text.strip()): return True
    return False

def extract_exercises():
    doc = fitz.open(PDF_PATH)
    all_chapters = []

    for i, start_page in enumerate(EXERCISE_STARTS):
        chapter_idx = i + 1
        q_prefix = f"{chapter_idx}."
        
        start_0 = start_page - 1
        
        # Set a safe limit (e.g., 10 pages max for exercises, or until next chapter)
        # Next start page is a hard limit
        if i < len(EXERCISE_STARTS) - 1:
            next_start = EXERCISE_STARTS[i+1] - 1
            limit = min(start_0 + 10, next_start)
        else:
            limit = min(start_0 + 10, len(doc))
            
        print(f"Scanning Chapter {chapter_idx} Exercises (Start Page {start_page})...")
        
        questions = []
        current_q = None
        
        stop_chapter = False

        for p in range(start_0, limit):
            if stop_chapter: break
            
            page = doc[p]
            blocks = page.get_text("dict")["blocks"]
            blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))
            
            for block in blocks:
                if "lines" not in block: continue
                
                for line in block["lines"]:
                    line_text = " ".join([s["text"] for s in line["spans"]]).strip()
                    
                    if not line_text: continue
                    
                    # Stop conditions
                    if "Answers to Some Intext Questions" in line_text:
                        stop_chapter = True
                        break
                    
                    # Check for Next Chapter Start (BallroomTango check would be ideal but text availability is fine)
                    if line_text.startswith("Unit ") and "Objectives" in page.get_text("text"):
                         stop_chapter = True
                         break

                    # Detect Question Start: "1.1 text", "1.10 text"
                    # We match strictly the chapter prefix
                    match = re.match(rf'^({chapter_idx}\.\d+)', line_text)
                    if match:
                        if current_q:
                            questions.append(current_q.strip())
                        current_q = line_text
                        continue
                    
                    # Continuation
                    if current_q:
                        if not is_noise(line_text):
                            current_q += " " + line_text
                            
                if stop_chapter: break
        
        if current_q:
            questions.append(current_q.strip())
            
        all_chapters.append((chapter_idx, questions))
        
    print(f"Writing to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ch, qs in all_chapters:
            f.write(f"\n\n========== CHAPTER {ch} ==========\n\n")
            if not qs:
                f.write("[No questions found for this chapter]\n")
            for q in qs:
                q = re.sub(r'\s+', ' ', q)
                f.write(q + "\n\n")

    print(f"✅ Extracted exercises for {len(all_chapters)} chapters.")
    
if __name__ == "__main__":
    extract_exercises()
