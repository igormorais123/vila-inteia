-- Vila INTEIA - Political Forecasts (BR 2026)
-- Schema for the political-prediction product. Multi-tenant via vila_clients.

create extension if not exists "uuid-ossp";

-- ============================================================
-- Calendar of elections
-- ============================================================
create table if not exists vila_election_calendar (
  id              uuid primary key default uuid_generate_v4(),
  election_date   date not null,
  cargo           text not null
                  check (cargo in ('presidente','governador','senador',
                                   'deputado_federal','deputado_estadual',
                                   'prefeito','vereador','impeachment',
                                   'legislativo','outro')),
  uf              char(2),                  -- null for federal
  turno           smallint check (turno in (1,2)),
  total_seats     integer,
  metadata        jsonb default '{}'::jsonb,
  created_at      timestamptz default now()
);

create index if not exists idx_election_cargo_date on vila_election_calendar(cargo, election_date);

-- ============================================================
-- Candidates
-- ============================================================
create table if not exists vila_candidates (
  id              uuid primary key default uuid_generate_v4(),
  election_id     uuid references vila_election_calendar(id) on delete cascade,
  registry_id     text unique,              -- e.g. 'lula_2026'
  tse_id          text,                     -- TSE numero registro (when known)
  nome            text not null,
  partido         text not null,
  coligacao       text,
  uf              char(2),
  incumbente      boolean default false,
  regime          text check (regime in ('left','right','center','pop_left','pop_right')),
  metadata        jsonb default '{}'::jsonb
);

create index if not exists idx_candidate_election on vila_candidates(election_id);
create index if not exists idx_candidate_registry on vila_candidates(registry_id);

-- ============================================================
-- Polls (raw)
-- ============================================================
create table if not exists vila_polls (
  id              uuid primary key default uuid_generate_v4(),
  election_id     uuid references vila_election_calendar(id) on delete cascade,
  instituto       text not null,
  data_inicio     date not null,
  data_fim        date not null,
  data_publicacao date,
  metodologia     text check (metodologia in ('cati','face_to_face','rds',
                                              'mixed','online_panel','telefone')),
  sample_n        integer,
  margin_error    numeric,
  topline         jsonb not null,           -- {candidate_registry_id: pct}
  scenario        text,
  source_url      text,
  registered_tse  text,
  ingested_at     timestamptz default now()
);

create index if not exists idx_poll_election on vila_polls(election_id);
create index if not exists idx_poll_pub      on vila_polls(data_publicacao desc);

-- ============================================================
-- Forecasts (predictions persisted)
-- ============================================================
create table if not exists vila_forecasts (
  id                  uuid primary key default uuid_generate_v4(),
  client_id           uuid references vila_clients(id) on delete set null,
  election_id         uuid references vila_election_calendar(id) on delete cascade,
  candidate_id        uuid references vila_candidates(id) on delete cascade,
  horizon_days        integer not null,
  p_raw               numeric,
  p_calibrated        numeric,
  p_lo                numeric,
  p_hi                numeric,
  cohort_tier         text,
  cohort_n            integer,
  ensemble_weights    jsonb,
  features_snapshot   jsonb,
  model_version       text,
  predicted_at        timestamptz default now()
);

create index if not exists idx_forecast_election on vila_forecasts(election_id, predicted_at desc);
create index if not exists idx_forecast_client   on vila_forecasts(client_id, predicted_at desc);

-- ============================================================
-- Official results (post-election)
-- ============================================================
create table if not exists vila_election_results (
  id              uuid primary key default uuid_generate_v4(),
  election_id     uuid references vila_election_calendar(id) on delete cascade,
  candidate_id    uuid references vila_candidates(id) on delete cascade,
  votos_validos   integer,
  pct_validos     numeric,
  classificacao   integer,
  eleito          boolean,
  resolved_at     timestamptz default now()
);

-- ============================================================
-- Multi-tenant clients
-- ============================================================
create table if not exists vila_clients (
  id              uuid primary key default uuid_generate_v4(),
  nome            text not null,
  api_key_hash    text unique not null,
  plan            text check (plan in ('free','pro','enterprise')) default 'free',
  rate_limit_rpm  integer default 60,
  metadata        jsonb default '{}'::jsonb,
  created_at      timestamptz default now()
);

create table if not exists vila_client_usage (
  id              uuid primary key default uuid_generate_v4(),
  client_id       uuid references vila_clients(id) on delete cascade,
  endpoint        text,
  bytes_returned  integer,
  status_code     integer,
  ts              timestamptz default now()
);

create index if not exists idx_usage_client_ts on vila_client_usage(client_id, ts desc);

-- ============================================================
-- Cohort fit snapshots (for reproducibility)
-- ============================================================
create table if not exists vila_cohort_fits (
  id              uuid primary key default uuid_generate_v4(),
  fit_name        text not null,
  fit_version     text not null,
  rates_json      jsonb not null,
  n_train         integer,
  brier_train     numeric,
  brier_holdout   numeric,
  acc_train       numeric,
  acc_holdout     numeric,
  fitted_at       timestamptz default now(),
  unique(fit_name, fit_version)
);
