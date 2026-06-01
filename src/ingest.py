"""Ingest documents from data/ into Postgres: chunk -> embed -> upsert.

Usage:
    python -m src.ingest                # ingest everything under data/
    python -m src.ingest data/foo.md    # ingest specific files
"""
from __future__ import annotations

import sys
from pathlib import Path

from .chunk import chunk_text
from .db import connect
from .embed import embed_texts

DATA_DIR = Path("data")
TEXT_SUFFIXES = {".md", ".txt"}


def _iter_files(args: list[str]) -> list[Path]:
    if args:
        return [Path(a) for a in args]
    return sorted(p for p in DATA_DIR.rglob("*") if p.suffix.lower() in TEXT_SUFFIXES)


def ingest_file(conn, path: Path) -> int:
    text = path.read_text(encoding="utf-8")
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
    files = _iter_files(argv)
    if not files:
        print(f"No .md/.txt files found under {DATA_DIR}/")
        return

    with connect() as conn:
        total = 0
        for path in files:
            if not path.exists():
                print(f"  skip (missing): {path}")
                continue
            n = ingest_file(conn, path)
            total += n
            print(f"  {path}: {n} chunks")
        print(f"Done. {total} chunks across {len(files)} file(s).")


if __name__ == "__main__":
    main(sys.argv[1:])
