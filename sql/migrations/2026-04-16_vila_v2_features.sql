-- =========================================================
-- Vila INTEIA v2: save/load, constituição viva, economia, Chateaubriand
-- Data: 2026-04-16
-- Projeto Supabase: conecta-2026 (dvgbqbwipwegkndutvte)
-- JÁ APLICADO em 2026-04-16 via MCP Supabase.
-- Este arquivo existe como registro versionado.
-- =========================================================

CREATE TABLE IF NOT EXISTS public.vila_instancias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    descricao TEXT,
    pacote_base TEXT NOT NULL,
    qtd_habitantes INTEGER NOT NULL DEFAULT 100,
    objetivo TEXT,
    status TEXT NOT NULL DEFAULT 'ativa'
        CHECK (status IN ('ativa','pausada','arquivada','finalizada')),
    step_atual INTEGER NOT NULL DEFAULT 0,
    hora_virtual TIMESTAMPTZ,
    metadados JSONB NOT NULL DEFAULT '{}'::JSONB,
    criada_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizada_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    pausada_em TIMESTAMPTZ,
    criada_por TEXT
);
CREATE INDEX IF NOT EXISTS idx_vila_instancias_status ON public.vila_instancias(status);

CREATE TABLE IF NOT EXISTS public.vila_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vila_id UUID NOT NULL REFERENCES public.vila_instancias(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'auto'
        CHECK (tipo IN ('auto','manual','checkpoint')),
    estado JSONB NOT NULL,
    tamanho_bytes INTEGER,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_vila_snapshots_vila
    ON public.vila_snapshots(vila_id, step DESC);

CREATE TABLE IF NOT EXISTS public.vila_constituicao_artigos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vila_id UUID REFERENCES public.vila_instancias(id) ON DELETE CASCADE,
    numero INTEGER NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('operacional','economico','estrutural')),
    titulo TEXT NOT NULL,
    texto TEXT NOT NULL,
    justificativa TEXT,
    proposto_por TEXT,
    evento_origem TEXT,
    status TEXT NOT NULL DEFAULT 'proposto'
        CHECK (status IN ('proposto','em_votacao','aprovado','rejeitado','vigente','revogado')),
    votos_favor INTEGER DEFAULT 0,
    votos_contra INTEGER DEFAULT 0,
    votos_abstencao INTEGER DEFAULT 0,
    quorum_necessario INTEGER DEFAULT 0,
    promulgado_em TIMESTAMPTZ,
    revogado_em TIMESTAMPTZ,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_artigos_vila
    ON public.vila_constituicao_artigos(vila_id, status);

CREATE TABLE IF NOT EXISTS public.vila_constituicao_votos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artigo_id UUID NOT NULL REFERENCES public.vila_constituicao_artigos(id) ON DELETE CASCADE,
    agente_id TEXT NOT NULL,
    agente_nome TEXT,
    voto TEXT NOT NULL CHECK (voto IN ('favor','contra','abstencao')),
    justificativa TEXT,
    votado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(artigo_id, agente_id)
);

CREATE TABLE IF NOT EXISTS public.vila_tickets_executivo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vila_id UUID REFERENCES public.vila_instancias(id) ON DELETE CASCADE,
    artigo_id UUID REFERENCES public.vila_constituicao_artigos(id) ON DELETE SET NULL,
    titulo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    tipo TEXT NOT NULL,
    urgencia INTEGER NOT NULL DEFAULT 3 CHECK (urgencia BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'aberto'
        CHECK (status IN ('aberto','em_analise','implementado','rejeitado','adiado')),
    resposta_executivo TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    respondido_em TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.vila_economia_perfis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vila_id UUID REFERENCES public.vila_instancias(id) ON DELETE CASCADE,
    agente_id TEXT NOT NULL,
    ambicao_financeira NUMERIC(4,3) NOT NULL DEFAULT 0.500
        CHECK (ambicao_financeira BETWEEN 0 AND 1),
    propensao_risco NUMERIC(4,3) NOT NULL DEFAULT 0.500,
    valor_reserva NUMERIC(12,2) NOT NULL DEFAULT 0,
    especialidades TEXT[],
    historico_ganhos NUMERIC(12,2) NOT NULL DEFAULT 0,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(vila_id, agente_id)
);

ALTER TABLE public.vila_transacoes
    ADD COLUMN IF NOT EXISTS vila_id UUID REFERENCES public.vila_instancias(id) ON DELETE CASCADE;
ALTER TABLE public.vila_transacoes
    ADD COLUMN IF NOT EXISTS tipo TEXT;
ALTER TABLE public.vila_transacoes
    ADD COLUMN IF NOT EXISTS contexto JSONB DEFAULT '{}'::JSONB;

CREATE TABLE IF NOT EXISTS public.vila_submissoes_mirante (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vila_id UUID REFERENCES public.vila_instancias(id) ON DELETE CASCADE,
    agente_id TEXT NOT NULL,
    agente_nome TEXT,
    titulo TEXT NOT NULL,
    slug TEXT,
    categoria TEXT,
    corpo_original TEXT NOT NULL,
    corpo_final TEXT,
    tags TEXT[],
    parecer_chateaubriand JSONB,
    status TEXT NOT NULL DEFAULT 'submetido' CHECK (status IN (
        'submetido','em_analise','aprovado_chefe','reescrito',
        'enviado_mirante','publicado','bloqueado_mirante','rejeitado','arquivado'
    )),
    url_mirante TEXT,
    motivo_bloqueio TEXT,
    tentativas INTEGER NOT NULL DEFAULT 0,
    submetido_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    processado_em TIMESTAMPTZ,
    publicado_em TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_submissoes_vila_status
    ON public.vila_submissoes_mirante(vila_id, status);

CREATE TABLE IF NOT EXISTS public.vila_pacotes_habitantes (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    total_agentes INTEGER,
    arquivo_origem TEXT,
    tipo TEXT CHECK (tipo IN ('eleitores','consultores','magistrados','parlamentares','gestores','arquetipos','misto')),
    metadados JSONB DEFAULT '{}'::JSONB,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO public.vila_pacotes_habitantes (id, nome, descricao, tipo) VALUES
    ('eleitores-df-2015', 'Eleitores sintéticos DF', '1015 eleitores sintéticos do DF', 'eleitores'),
    ('eleitores-rr-1000', 'Eleitores sintéticos RR', '1000 eleitores sintéticos de RR', 'eleitores'),
    ('consultores-lendarios', 'Consultores lendários', '158 consultores', 'consultores'),
    ('magistrados', 'Magistrados', '164 perfis sintéticos de juízes', 'magistrados'),
    ('parlamentares-df', 'Parlamentares DF', 'Câmara, Senado, CLDF', 'parlamentares'),
    ('gestores-publicos', 'Gestores públicos', 'Administração pública', 'gestores'),
    ('arquetipos-base', 'Arquétipos base', 'Pack mínimo genérico', 'arquetipos')
ON CONFLICT (id) DO UPDATE SET atualizado_em = now();

-- RLS permissiva (dev). Endurecer antes de produção multi-tenant.
ALTER TABLE public.vila_instancias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_constituicao_artigos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_constituicao_votos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_tickets_executivo ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_economia_perfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_submissoes_mirante ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vila_pacotes_habitantes ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'vila_instancias','vila_snapshots','vila_constituicao_artigos',
    'vila_constituicao_votos','vila_tickets_executivo','vila_economia_perfis',
    'vila_submissoes_mirante','vila_pacotes_habitantes'
  ]) LOOP
    EXECUTE format('DROP POLICY IF EXISTS "anon_all_%1$s" ON public.%1$I', t);
    EXECUTE format('CREATE POLICY "anon_all_%1$s" ON public.%1$I FOR ALL USING (true) WITH CHECK (true)', t);
  END LOOP;
END $$;
