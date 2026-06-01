"""Document loaders: turn a file on disk into plain text for chunking.

Supports .md/.txt directly and .pdf via PyMuPDF (text layer). PDFs that are
scanned images have no text layer; those come back nearly empty and the caller
is expected to skip them (or OCR separately — see scripts/ocr_pdf.py).
"""
from __future__ import annotations

from pathlib import Path

# A file yielding fewer than this many characters is treated as "no text layer"
# (i.e. a scanned PDF that needs OCR) and skipped by the ingester.
MIN_TEXT_CHARS = 500

TEXT_SUFFIXES = {".md", ".txt"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | PDF_SUFFIXES


def read_pdf(path: Path) -> str:
    import fitz  # PyMuPDF; imported lazily so text-only use needs no PDF deps

    doc = fitz.open(path)
    try:
        pages = [page.get_text() for page in doc]
    finally:
        doc.close()
    return "\n\n".join(pages)


def _sanitize(text: str) -> str:
    # PostgreSQL text columns reject NUL (0x00) bytes, which PDF extraction can
    # emit. Strip them (plus the BOM) so any source is safe to store.
    return text.replace("\x00", "").replace("﻿", "")


def read_document(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _sanitize(path.read_text(encoding="utf-8", errors="ignore"))
    if suffix in PDF_SUFFIXES:
        return _sanitize(read_pdf(path))
    raise ValueError(f"Unsupported file type: {path.suffix} ({path})")


def looks_scanned(text: str) -> bool:
    return len(text.strip()) < MIN_TEXT_CHARS
