-- =========================================================
-- Mirante News: fila de submissões vindas da Vila INTEIA
-- Data: 2026-04-16
-- Projeto Supabase: mirante-news (fehdngdxmiuyksmstjyw)
-- JÁ APLICADO em 2026-04-16 via MCP Supabase.
-- =========================================================

CREATE TABLE IF NOT EXISTS public.mirante_submissoes_vila (
    submissao_id TEXT PRIMARY KEY,
    vila_id TEXT,
    slug TEXT NOT NULL,
    titulo TEXT NOT NULL,
    autor_nome TEXT,
    categoria TEXT,
    status TEXT NOT NULL DEFAULT 'recebido',
    url TEXT,
    motivo TEXT,
    recebido_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    publicado_em TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_mirante_sub_vila_publicado
    ON public.mirante_submissoes_vila(publicado_em DESC);
CREATE INDEX IF NOT EXISTS idx_mirante_sub_vila_vila
    ON public.mirante_submissoes_vila(vila_id, publicado_em DESC);

ALTER TABLE public.mirante_submissoes_vila ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_mirante_sub_vila"
    ON public.mirante_submissoes_vila;
CREATE POLICY "service_role_all_mirante_sub_vila"
    ON public.mirante_submissoes_vila
    FOR ALL USING (true) WITH CHECK (true);
