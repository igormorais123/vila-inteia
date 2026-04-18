-- Migration 001 — vila_traces
-- Onda 2 do HARNESS_VILA.md (Gap #1 — Observabilidade estruturada).
-- Executar no Supabase SQL Editor do projeto conecta-2026.
--
-- Modo shadow: engine/harness/observabilidade.py escreve aqui sem
-- alterar comportamento do loop cognitivo. Se esta tabela não existir,
-- os inserts falham silenciosamente e o sistema segue normal.

CREATE TABLE IF NOT EXISTS vila_traces (
    trace_id          text PRIMARY KEY,
    step              integer NOT NULL,
    agente_id         text NOT NULL,
    fase              text NOT NULL,          -- perceber|recuperar|planejar|executar|conversar|refletir|sintetizar|skill|protocolo|tool
    inicio            timestamptz NOT NULL,
    fim               timestamptz NOT NULL,
    duracao_ms        integer NOT NULL,
    inputs_hash       text,
    outputs_hash      text,
    causal_parent     text REFERENCES vila_traces(trace_id) ON DELETE SET NULL,
    tokens_consumidos integer DEFAULT 0,
    custo_usd         numeric(10, 6) DEFAULT 0,
    ferramenta_chamada text,
    resultado         text NOT NULL DEFAULT 'sucesso', -- sucesso|falha|aprovacao_humana|retry|vazio
    metadata          jsonb DEFAULT '{}'::jsonb,
    created_at        timestamptz DEFAULT now()
);

-- Índices para as queries mais comuns da Torre do Observatório
CREATE INDEX IF NOT EXISTS idx_vila_traces_step ON vila_traces(step DESC);
CREATE INDEX IF NOT EXISTS idx_vila_traces_agente_step ON vila_traces(agente_id, step DESC);
CREATE INDEX IF NOT EXISTS idx_vila_traces_fase ON vila_traces(fase);
CREATE INDEX IF NOT EXISTS idx_vila_traces_causal ON vila_traces(causal_parent);
CREATE INDEX IF NOT EXISTS idx_vila_traces_inicio ON vila_traces(inicio DESC);
CREATE INDEX IF NOT EXISTS idx_vila_traces_resultado ON vila_traces(resultado) WHERE resultado <> 'sucesso';

-- Policy permissiva (mesmo padrão das outras tabelas vila_*)
ALTER TABLE vila_traces ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "vila_traces_rw" ON vila_traces;
CREATE POLICY "vila_traces_rw"
    ON vila_traces
    FOR ALL
    USING (true)
    WITH CHECK (true);

COMMENT ON TABLE vila_traces IS
    'Trace estruturado por fase cognitiva. Onda 2 do HARNESS_VILA.md. '
    'Alimenta Torre do Observatório + Mercado da Atenção + relatórios '
    'operacionais. Ver engine/harness/observabilidade.py.';
