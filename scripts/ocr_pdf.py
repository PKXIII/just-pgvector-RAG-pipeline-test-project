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

Output is denoised (see `_denoise`) to drop OCR debris from shredded Thai
diacritics before it is written.
"""
from __future__ import annotations

import sys
from pathlib import Path

OUT_DIR = Path("ocr_text")
DPI = 300          # higher = better OCR, slower
LANG = "tha+eng"   # Thai + English


def _denoise(text: str) -> str:
    """Drop OCR-debris lines: scattered single/double-character tokens that
    appear when Thai diacritics get shredded by the scan. Real Thai content is
    one long space-free run, and English words average ~5 chars, so a line of
    many tiny tokens (avg length <= 1.6) is almost always garbage.
    """
    out = []
    for line in text.splitlines():
        toks = line.split()
        if len(toks) >= 3 and sum(len(t) for t in toks) / len(toks) <= 1.6:
            continue
        out.append(line)
    return "\n".join(out)


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
    cleaned = _denoise("\n\n".join(parts))
    out.write_text(cleaned, encoding="utf-8")
    print(f"\n  -> {out}  ({len(cleaned)} chars after denoise)")
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
