-- pgvector RAG schema
-- Run as a Postgres superuser against the target database (see scripts/setup_db.sh).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          BIGSERIAL PRIMARY KEY,
    source      TEXT        NOT NULL,           -- file the chunk came from
    chunk_index INT         NOT NULL,           -- position within that file
    content     TEXT        NOT NULL,           -- the chunk text
    embedding   vector(1024),                   -- bge-m3 = 1024 dims (keep in sync with EMBED_DIM)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, chunk_index)
);

-- Approximate nearest-neighbour index for cosine distance.
-- HNSW gives fast recall; fine to create up front on a small table.
CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING hnsw (embedding vector_cosine_ops);
