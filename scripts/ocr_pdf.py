"""Optional OCR for scanned PDFs (no text layer) -> .txt in ocr_text/.

Four of the theses in this corpus are scanned images. This renders each page
with PyMuPDF and OCRs it with Tesseract (Thai + English), writing one .txt per
PDF that you can then ingest like any other text file.

Prerequisites (Debian/Ubuntu):
    sudo apt-get install -y tesseract-ocr tesseract-ocr-tha
    pip install pytesseract pillow

Usage:
    python scripts/ocr_pdf.py "literature_review/2545 ... .pdf" [more.pdf ...]
    python -m src.ingest ocr_text          # then ingest the OCR output
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT_DIR = Path("ocr_text")
DPI = 300          # higher = better OCR, slower
LANG = "tha+eng"   # Thai + English


def ocr_pdf(path: Path) -> Path:
    import fitz
    import pytesseract
    from PIL import Image

    OUT_DIR.mkdir(exist_ok=True)
    doc = fitz.open(path)
    parts: list[str] = []
    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=DPI)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            parts.append(pytesseract.image_to_string(img, lang=LANG))
            print(f"  {path.name}: page {i + 1}/{doc.page_count}", end="\r")
    finally:
        doc.close()

    out = OUT_DIR / (path.stem + ".txt")
    out.write_text("\n\n".join(parts), encoding="utf-8")
    print(f"\n  -> {out}  ({sum(len(p) for p in parts)} chars)")
    return out


def main(argv: list[str]) -> None:
    if not argv:
        print('Usage: python scripts/ocr_pdf.py "scanned.pdf" [more.pdf ...]')
        return
    for a in argv:
        p = Path(a)
        if not p.exists():
            print(f"  skip (missing): {p}")
            continue
        ocr_pdf(p)


if __name__ == "__main__":
    main(sys.argv[1:])
