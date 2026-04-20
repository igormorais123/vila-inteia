-- Onda 14 — Persistência da trajetória psico-histórica

CREATE TABLE IF NOT EXISTS vila_trajetoria_psico (
    id              BIGSERIAL PRIMARY KEY,
    vila_id         UUID NOT NULL,
    step            INTEGER NOT NULL,
    estado          TEXT NOT NULL,
    polarizacao     FLOAT NOT NULL DEFAULT 0.0,
    gini            FLOAT NOT NULL DEFAULT 0.0,
    n_ativos        INTEGER NOT NULL DEFAULT 0,
    n_latentes      INTEGER NOT NULL DEFAULT 0,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (vila_id, step)
);

CREATE INDEX IF NOT EXISTS idx_traj_psico_vila_step
    ON vila_trajetoria_psico (vila_id, step);
CREATE INDEX IF NOT EXISTS idx_traj_psico_estado
    ON vila_trajetoria_psico (estado);

ALTER TABLE vila_trajetoria_psico ENABLE ROW LEVEL SECURITY;
CREATE POLICY anon_all_traj ON vila_trajetoria_psico FOR ALL USING (true);
