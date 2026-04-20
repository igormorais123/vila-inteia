-- Onda 6 — GraphRAG schema no Supabase
-- Apply via MCP ou psql

CREATE TABLE IF NOT EXISTS vila_grafo_nos (
    id              TEXT PRIMARY KEY,
    vila_id         UUID NOT NULL,
    tipo            TEXT NOT NULL,
    rotulo          TEXT NOT NULL,
    props           JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_grafo_nos_vila_tipo
    ON vila_grafo_nos (vila_id, tipo);
CREATE INDEX IF NOT EXISTS idx_grafo_nos_rotulo
    ON vila_grafo_nos USING gin (rotulo gin_trgm_ops);

CREATE TABLE IF NOT EXISTS vila_grafo_arestas (
    id              BIGSERIAL PRIMARY KEY,
    vila_id         UUID NOT NULL,
    origem          TEXT NOT NULL REFERENCES vila_grafo_nos(id) ON DELETE CASCADE,
    destino         TEXT NOT NULL REFERENCES vila_grafo_nos(id) ON DELETE CASCADE,
    relacao         TEXT NOT NULL,
    peso            FLOAT NOT NULL DEFAULT 1.0,
    props           JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_grafo_arestas_vila
    ON vila_grafo_arestas (vila_id);
CREATE INDEX IF NOT EXISTS idx_grafo_arestas_origem
    ON vila_grafo_arestas (origem);
CREATE INDEX IF NOT EXISTS idx_grafo_arestas_destino
    ON vila_grafo_arestas (destino);

-- Permissões padrão (reforçar em produção)
ALTER TABLE vila_grafo_nos    ENABLE ROW LEVEL SECURITY;
ALTER TABLE vila_grafo_arestas ENABLE ROW LEVEL SECURITY;
CREATE POLICY anon_all_nos     ON vila_grafo_nos     FOR ALL USING (true);
CREATE POLICY anon_all_arestas ON vila_grafo_arestas FOR ALL USING (true);
