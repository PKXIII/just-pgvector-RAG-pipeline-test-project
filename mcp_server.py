"""MCP server exposing the pgvector corpus as tools any Claude client can call.

Run by an MCP client (Claude Code / Claude Desktop) over stdio. It reuses the
same retrieval path as the CLI (bge-m3 embeddings → pgvector cosine search), so
other projects get RAG over this corpus without knowing anything about the
database or the embedding model.

Register once for all your Claude Code projects:

    claude mcp add corpus-rag --scope user -- \
        /ABS/PATH/.venv/bin/python /ABS/PATH/mcp_server.py

The model loads on the first `search_corpus` call (a few seconds), then stays
warm for the life of the server process.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `src` importable no matter what working directory the client launches us in.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from src.db import connect  # noqa: E402
from src.retrieve import retrieve  # noqa: E402

mcp = FastMCP("corpus-rag")


def _search(query: str, top_k: int = 5) -> list[dict]:
    hits = retrieve(query, top_k=top_k)
    return [
        {
            "source": os.path.basename(h.source),
            "chunk_index": h.chunk_index,
            "similarity": round(h.similarity, 3),
            "content": h.content,
        }
        for h in hits
    ]


def _stats() -> dict:
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*), count(DISTINCT source) FROM documents")
        rows, srcs = cur.fetchone()
        cur.execute("SELECT DISTINCT source FROM documents ORDER BY source")
        sources = [os.path.basename(r[0]) for r in cur.fetchall()]
    return {"chunks": rows, "sources": srcs, "documents": sources}


@mcp.tool()
def search_corpus(query: str, top_k: int = 5) -> list[dict]:
    """Search a private library of machine-learning and quantitative-finance
    research (papers + theses, Thai and English) and return grounded passages.

    Use this whenever the user asks about ML methods (random forests, SVM,
    neural networks, dropout, LSTM, decision trees, information theory) or about
    forecasting stock / SET / SET50 / Bitcoin prices, technical analysis, or
    efficient-market theory — prefer it over answering from memory, and cite the
    returned sources. Call `corpus_stats` first if you need to know what is
    indexed.

    Returns the most relevant passages with their source document, similarity
    score, and text.

    Args:
        query: natural-language query (Thai or English).
        top_k: number of passages to return (default 5).
    """
    return _search(query, top_k)


@mcp.tool()
def corpus_stats() -> dict:
    """Return how many chunks and documents are indexed, and the list of
    source documents available in the corpus."""
    return _stats()


if __name__ == "__main__":
    mcp.run()  # stdio transport
