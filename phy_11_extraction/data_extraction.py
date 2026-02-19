import sys
import fitz
import pytesseract
from PIL import Image
from tqdm import tqdm

pdf_path = sys.argv[1] if len(sys.argv) > 1 else "dataset/Physics-11.pdf"

doc = fitz.open(pdf_path)
all_text = []

for page in tqdm(doc, total=len(doc)):
    rect = page.rect
    header = rect.height * 0.08
    footer = rect.height * 0.08
    clip = fitz.Rect(rect.x0, rect.y0 + header, rect.x1, rect.y1 - footer)
    pix = page.get_pixmap(dpi=300, clip=clip)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(image=img,config="--oem 1")
    all_text.append(text)

with open("p_11_kb/information.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(all_text))

print("✅ Done. Saved to p_11_kb/information.txt")
