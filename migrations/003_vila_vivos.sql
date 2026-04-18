-- Migration 003 — vila_vivos (heartbeats + coluna diária)
-- Aplicada via MCP no Supabase conecta-2026 em 2026-04-18.
-- Ver engine/agentes_vivos/ e engine/coluna_vila.py.

-- Heartbeats dos agentes vivos (Helena, Efesto, futuros)
CREATE TABLE IF NOT EXISTS vila_heartbeat (
    heartbeat_id   text PRIMARY KEY,
    agente         text NOT NULL,
    step           integer NOT NULL,
    executado_em   timestamptz NOT NULL,
    duracao_ms     integer NOT NULL DEFAULT 0,
    resultado      text NOT NULL DEFAULT 'ok',        -- ok | alerta | falha
    acoes          jsonb DEFAULT '[]'::jsonb,
    alertas        jsonb DEFAULT '[]'::jsonb,
    metricas       jsonb DEFAULT '{}'::jsonb,
    created_at     timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vh_agente_exec ON vila_heartbeat(agente, executado_em DESC);
CREATE INDEX IF NOT EXISTS idx_vh_resultado   ON vila_heartbeat(resultado) WHERE resultado <> 'ok';

ALTER TABLE vila_heartbeat ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "vila_heartbeat_rw" ON vila_heartbeat;
CREATE POLICY "vila_heartbeat_rw" ON vila_heartbeat FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE vila_heartbeat IS
    'Pulsos dos agentes vivos da INTEIA (Helena, Efesto). Cada linha traz '
    'ações executadas, alertas e métricas coletadas no heartbeat. '
    'Ver engine/agentes_vivos/.';


-- Coluna diária Vila no Mirante News
CREATE TABLE IF NOT EXISTS vila_coluna_publicacoes (
    publicacao_id   text PRIMARY KEY,
    data_ref        date NOT NULL,
    autor_id        text NOT NULL,
    autor_nome      text NOT NULL,
    titulo          text NOT NULL,
    slug            text NOT NULL,
    categoria       text NOT NULL,
    resultado       jsonb DEFAULT '{}'::jsonb,
    material_resumo jsonb DEFAULT '{}'::jsonb,
    publicado_em    timestamptz NOT NULL DEFAULT now()
);

-- garante 1 publicação/dia
CREATE UNIQUE INDEX IF NOT EXISTS uq_coluna_data ON vila_coluna_publicacoes(data_ref);
CREATE INDEX IF NOT EXISTS idx_coluna_publ      ON vila_coluna_publicacoes(publicado_em DESC);

ALTER TABLE vila_coluna_publicacoes ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "vila_coluna_rw" ON vila_coluna_publicacoes;
CREATE POLICY "vila_coluna_rw" ON vila_coluna_publicacoes FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE vila_coluna_publicacoes IS
    'Uma linha por dia de coluna da Vila no Mirante. Assinada por Helena '
    'ou Efesto. Unique (data_ref) garante idempotência diária. '
    'Ver engine/coluna_vila.py.';
