-- Migration 004 — remove FK em causal_parent.
-- Fases-filhas são persistidas antes do trace pai (contexto só fecha no exit),
-- a FK causava rejeição silenciosa dos inserts. Mantemos só o índice.

ALTER TABLE vila_traces DROP CONSTRAINT IF EXISTS vila_traces_causal_parent_fkey;

COMMENT ON COLUMN vila_traces.causal_parent IS
    'Correlation ID (trace_id do pai). Sem FK por causa do ordering: pais são '
    'escritos depois dos filhos (scope fecha no exit do context manager).';
