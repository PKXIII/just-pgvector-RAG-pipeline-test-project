"""End-to-end RAG: retrieve from pgvector, then answer with Claude.

Usage:
    python -m src.ask "นโยบายนี้คุ้มครองอะไรบ้าง?"
    python -m src.ask "What is the waiting period?"
"""
from __future__ import annotations

import sys

from anthropic import Anthropic

from .config import config
from .retrieve import Hit, retrieve

SYSTEM_PROMPT = (
    "You are a precise retrieval-grounded assistant. Answer ONLY from the "
    "provided context passages. Cite the passages you use as [n]. If the answer "
    "is not in the context, say you don't know — do not guess. Reply in the same "
    "language as the user's question (Thai or English)."
)


def _format_context(hits: list[Hit]) -> str:
    blocks = []
    for i, h in enumerate(hits, start=1):
        blocks.append(f"[{i}] (source: {h.source}#{h.chunk_index})\n{h.content}")
    return "\n\n".join(blocks)


def ask(question: str) -> str:
    if not config.anthropic_api_key:
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set. Add it to .env "
            "(get one at https://console.anthropic.com)."
        )

    hits = retrieve(question)
    if not hits:
        return "No documents indexed yet — run `python -m src.ingest` first."

    context = _format_context(hits)
    client = Anthropic(api_key=config.anthropic_api_key)

    message = client.messages.create(
        model=config.claude_model,
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                # Stable instructions are cached across calls to cut input cost.
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Context passages:\n\n{context}\n\n"
                    f"Question: {question}"
                ),
            }
        ],
    )

    answer = "".join(b.text for b in message.content if b.type == "text")

    sources = "\n".join(
        f"  [{i}] {h.source}#{h.chunk_index}  (sim {h.similarity:.3f})"
        for i, h in enumerate(hits, start=1)
    )
    return f"{answer}\n\nSources:\n{sources}"


def main(argv: list[str]) -> None:
    question = " ".join(argv).strip()
    if not question:
        print('Usage: python -m src.ask "your question"')
        return
    print(ask(question))


if __name__ == "__main__":
    main(sys.argv[1:])
