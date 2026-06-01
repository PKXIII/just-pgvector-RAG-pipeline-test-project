"""Simple, language-agnostic text chunking.

Splits on blank lines first (paragraphs), then packs paragraphs into windows of
roughly `chunk_size` characters with `chunk_overlap` characters of overlap so a
fact that straddles a boundary still lands whole in at least one chunk.
Character-based (not token-based) on purpose: it works the same for Thai, which
has no word spaces, as it does for English.
"""
from __future__ import annotations

import re

from .config import config


def _paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_text(
    text: str,
    size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    size = size or config.chunk_size
    overlap = overlap or config.chunk_overlap

    chunks: list[str] = []
    buf = ""
    for para in _paragraphs(text):
        # A single oversized paragraph is hard-split on character windows.
        if len(para) > size:
            if buf:
                chunks.append(buf)
                buf = ""
            for i in range(0, len(para), size - overlap):
                chunks.append(para[i : i + size])
            continue

        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}" if buf else para
        else:
            chunks.append(buf)
            # carry the tail of the previous chunk forward as overlap
            tail = buf[-overlap:] if overlap else ""
            buf = f"{tail}\n\n{para}" if tail else para

    if buf:
        chunks.append(buf)
    return chunks
