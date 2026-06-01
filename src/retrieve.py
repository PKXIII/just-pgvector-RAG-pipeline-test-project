"""Vector retrieval against pgvector using cosine distance."""
from __future__ import annotations

from dataclasses import dataclass

from .config import config
from .db import connect
from .embed import embed_query


@dataclass
class Hit:
    source: str
    chunk_index: int
    content: str
    distance: float  # cosine distance; smaller = closer

    @property
    def similarity(self) -> float:
        return 1.0 - self.distance


def retrieve(query: str, top_k: int | None = None) -> list[Hit]:
    top_k = top_k or config.top_k
    qvec = embed_query(query)

    with connect() as conn, conn.cursor() as cur:
        # `<=>` is pgvector's cosine-distance operator; the HNSW index serves it.
        cur.execute(
            """
            SELECT source, chunk_index, content, embedding <=> %s::vector AS distance
            FROM documents
            ORDER BY distance ASC
            LIMIT %s
            """,
            (qvec, top_k),
        )
        rows = cur.fetchall()

    return [Hit(source=r[0], chunk_index=r[1], content=r[2], distance=float(r[3])) for r in rows]


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "test query"
    for h in retrieve(q):
        print(f"[{h.similarity:.3f}] {h.source}#{h.chunk_index}")
        print(f"    {h.content[:120]}…\n")
