"""Postgres connection helper with pgvector registered."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import psycopg
from pgvector.psycopg import register_vector

from .config import config


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Yield a connection that knows how to pass `vector` values to/from pgvector."""
    conn = psycopg.connect(config.conninfo)
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()
