-- On s'assure que l'extension pgvector est disponible
CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1 : les documents sources (1 ligne par article scrapé)
CREATE TABLE IF NOT EXISTS documents (
    id            SERIAL PRIMARY KEY,
    source_url    TEXT,
    titre         TEXT NOT NULL,
    categorie     TEXT,
    langue        TEXT DEFAULT 'fr',
    date_collecte DATE,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- Table 2 : les chunks (morceaux) + leur embedding vectoriel
CREATE TABLE IF NOT EXISTS chunks (
    id           SERIAL PRIMARY KEY,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index  INTEGER NOT NULL,
    content      TEXT NOT NULL,
    embedding    vector(384)          -- 384 = dimension du modèle e5-small
);

-- Index vectoriel pour une recherche par similarité rapide (distance cosinus)
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING hnsw (embedding vector_cosine_ops);
