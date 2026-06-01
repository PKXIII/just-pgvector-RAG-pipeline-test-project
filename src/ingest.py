"""Ingest documents into Postgres: load -> chunk -> embed -> upsert.

Supports .md / .txt / .pdf. Scanned PDFs (no text layer) are skipped with a
warning. Pass files or directories; directories are searched recursively.

Usage:
    python -m src.ingest                       # ingest $CORPUS_DIR (default: data/)
    python -m src.ingest literature_review     # ingest a whole folder
    python -m src.ingest data/foo.md a.pdf     # ingest specific files
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .chunk import chunk_text
from .db import connect
from .embed import embed_texts
from .loaders import SUPPORTED_SUFFIXES, looks_scanned, read_document

CORPUS_DIR = Path(os.getenv("CORPUS_DIR", "data"))


def _expand(arg: str) -> list[Path]:
    p = Path(arg)
    if p.is_dir():
        return sorted(f for f in p.rglob("*") if f.suffix.lower() in SUPPORTED_SUFFIXES)
    return [p]


def _collect(args: list[str]) -> list[Path]:
    if not args:
        return _expand(str(CORPUS_DIR))
    files: list[Path] = []
    for a in args:
        files.extend(_expand(a))
    return files


def ingest_file(conn, path: Path) -> int:
    text = read_document(path)
    if looks_scanned(text):
        print(f"  skip (scanned / no text layer, needs OCR): {path.name}")
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = embed_texts(chunks)
    source = str(path)

    with conn.cursor() as cur:
        # Re-ingest cleanly: drop prior chunks for this source first.
        cur.execute("DELETE FROM documents WHERE source = %s", (source,))
        for i, (content, emb) in enumerate(zip(chunks, embeddings)):
            cur.execute(
                """
                INSERT INTO documents (source, chunk_index, content, embedding)
                VALUES (%s, %s, %s, %s)
                """,
                (source, i, content, emb),
            )
    conn.commit()
    return len(chunks)


def main(argv: list[str]) -> None:
    files = _collect(argv)
    if not files:
        print(f"No supported files (.md/.txt/.pdf) found in {CORPUS_DIR}/")
        return

    with connect() as conn:
        total = 0
        for path in files:
            if not path.exists():
                print(f"  skip (missing): {path}")
                continue
            n = ingest_file(conn, path)
            total += n
            if n:
                print(f"  {path.name}: {n} chunks")
        print(f"Done. {total} chunks across {len(files)} file(s).")


if __name__ == "__main__":
    main(sys.argv[1:])
