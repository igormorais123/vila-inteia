-- Onda 106: backtest history persistence
-- Supabase: criar tabela vila_backtests

CREATE TABLE IF NOT EXISTS vila_backtests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  personas JSONB NOT NULL DEFAULT '[]'::jsonb,
  n_eventos INTEGER,
  n_datasets INTEGER,
  accuracy_global FLOAT,
  brier_vila FLOAT,
  brier_prior FLOAT,
  skill FLOAT,
  platt_a FLOAT,
  platt_b FLOAT,
  raw_payload JSONB
);

CREATE INDEX IF NOT EXISTS idx_vila_backtests_criado_em
  ON vila_backtests (criado_em DESC);

CREATE INDEX IF NOT EXISTS idx_vila_backtests_skill
  ON vila_backtests (skill DESC NULLS LAST);
