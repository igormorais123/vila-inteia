-- Migration 002 — vila_orcamento_historico
-- Onda 2 HARNESS_VILA.md (Gap #2 — Orçamento de contexto).
-- Alimenta o Mercado da Atenção com histórico de consumo por fase/agente.

CREATE TABLE IF NOT EXISTS vila_orcamento_historico (
    id                bigserial PRIMARY KEY,
    fase              text NOT NULL,
    agente_id         text NOT NULL,
    step              integer NOT NULL,
    tokens_consumidos integer NOT NULL DEFAULT 0,
    custo_usd         numeric(10, 6) NOT NULL DEFAULT 0,
    modelo            text,
    registrado_em     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_voh_agente_step ON vila_orcamento_historico(agente_id, step DESC);
CREATE INDEX IF NOT EXISTS idx_voh_fase        ON vila_orcamento_historico(fase);
CREATE INDEX IF NOT EXISTS idx_voh_registrado  ON vila_orcamento_historico(registrado_em DESC);

ALTER TABLE vila_orcamento_historico ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "voh_rw" ON vila_orcamento_historico;
CREATE POLICY "voh_rw" ON vila_orcamento_historico
    FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE vila_orcamento_historico IS
    'Consumo de tokens/custo por fase cognitiva e agente. Onda 2 HARNESS_VILA.md Gap #2. '
    'Alimenta Mercado da Atenção. Escritas via engine/harness/orcamento.py '
    '(só ativo com VILA_BUDGET_TRACK=1).';
