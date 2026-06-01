"""Central configuration, loaded from the environment (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Config:
    # Postgres
    pg_host: str = os.getenv("PGHOST", "localhost")
    pg_port: int = _int("PGPORT", 5432)
    pg_db: str = os.getenv("PGDATABASE", "ragdb")
    pg_user: str = os.getenv("PGUSER", "raguser")
    pg_password: str = os.getenv("PGPASSWORD", "ragpass")

    # Embeddings
    embed_model: str = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
    embed_dim: int = _int("EMBED_DIM", 1024)

    # Chunking
    chunk_size: int = _int("CHUNK_SIZE", 900)
    chunk_overlap: int = _int("CHUNK_OVERLAP", 150)

    # Retrieval
    top_k: int = _int("TOP_K", 5)

    # Generation
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    @property
    def conninfo(self) -> str:
        return (
            f"host={self.pg_host} port={self.pg_port} dbname={self.pg_db} "
            f"user={self.pg_user} password={self.pg_password}"
        )


config = Config()
