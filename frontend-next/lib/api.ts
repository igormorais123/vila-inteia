const BASE = process.env.VILA_API_BASE
  ? `${process.env.VILA_API_BASE}/api/v1/politica`
  : "/api/v1/politica";

export interface Candidate {
  id?: string;
  nome: string;
  partido: string;
  uf?: string;
  incumbente?: number;
  regime?: string;
  status?: "confirmed" | "speculation" | "ineligible";
  status_note?: string;
  p_winner?: number;
  p_raw?: number;
  p_cohort?: number;
  p_linzer?: number;
}

export interface Snapshot {
  predicted_at: string;
  election_date: string;
  horizon_days: number;
  candidates: Candidate[];
  method_note?: string;
}

export interface PredictResponse {
  p_cohort: number;
  p_linzer: number;
  p_blend: number;
  cohort_tier: string;
  cohort_n: number;
  horizon_days: number;
}

export interface QualityIndicator {
  n: number;
  acc: number;
  acc_wilson_95?: [number, number];
  brier: number;
  log_loss: number;
  brier_skill_vs_climatology?: number | null;
  auc?: number;
  ece?: number;
  mce?: number;
  mcc?: number;
  balanced_accuracy?: number;
  sensitivity?: number;
  specificity?: number;
  precision?: number;
  confusion?: { tp: number; fp: number; fn: number; tn: number };
}

export interface BacktestResponse {
  protocol?: string;
  source?: string;
  model_id?: string;
  summary?: { n: number; acc: number; brier: number; log_loss?: number };
  cycles?: { year: number; n: number; acc: number; brier: number; type: string }[];
  selective_sweep?: { tau: number; coverage: number; acc: number | null; n_kept: number; brier?: number }[];
  quality_indicators?: {
    baseline?: QualityIndicator;
    mrp?: QualityIndicator;
    lift_vs_baseline?: Record<string, number>;
    decision_edge?: { net_hits?: number; mcnemar_p?: number; dm_p_brier?: number };
  };
  statistical_tests?: {
    diebold_mariano?: Record<string, number | string>;
    mcnemar?: Record<string, number | string>;
  };
}

export interface EvolutionMetrics {
  n?: number;
  acc?: number;
  brier?: number;
  log_loss?: number;
  auc?: number;
  mcc?: number;
  ece?: number;
  score?: number;
  config?: Record<string, number>;
}

export interface EvolutionResponse {
  generated_at?: string;
  protocol?: string;
  methods?: string[];
  population_size?: number;
  generations?: number;
  seed?: number;
  active?: boolean;
  applied_at?: string;
  current_version?: string;
  gate?: {
    promoted?: boolean;
    reason?: string;
    checks?: Record<string, boolean>;
  };
  incumbent?: EvolutionMetrics;
  best?: EvolutionMetrics;
  leaderboard?: EvolutionMetrics[];
}

async function get<T>(path: string, apiKey?: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: apiKey ? { "X-API-Key": apiKey } : {},
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`API ${r.status} ${path}`);
  return r.json();
}

export const fetchPresidente = (k?: string) => get<Snapshot>("/predictions/presidente", k);
export const fetchSenador = (k?: string) => get<{ candidates: Candidate[] }>("/predictions/senador", k);
export const fetchAll = (k?: string) => get<any>("/predictions/all", k);
export const fetchHealth = () => get<{
  status: string;
  n_train_events: number;
  horizon_days: number;
  snapshot_predicted_at: string;
  validation_model?: string;
  validation_n?: number;
  validation_acc?: number;
  validation_brier?: number;
  validation_auc?: number;
  validation_mcc?: number;
  evolution_active?: boolean;
  evolution_promoted?: boolean;
  evolution_best_score?: number;
}>("/health");
export const fetchElections = () => get<{ election_date: string; cargos_supported: string[]; ufs_covered: string[] }>("/elections");
export const fetchBacktest = () => get<BacktestResponse>("/backtest");
export const fetchEvolution = () => get<EvolutionResponse>("/evolution");
export const fetchGovernadorByUf = (uf: string, k?: string) => get<{ uf: string; candidates: Candidate[] }>(`/predictions/governador?uf=${uf}`, k);
export const fetchGovernadorAll = (k?: string) => get<{ by_uf: Record<string, Candidate[]> }>("/predictions/governador", k);

export async function postPredict(req: {
  cargo: string; poll_lead_pp: number; days_to_election: number;
  incumbente: number; regime: string;
}, apiKey?: string): Promise<PredictResponse> {
  const r = await fetch(`${BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(apiKey ? { "X-API-Key": apiKey } : {}) },
    body: JSON.stringify(req),
  });
  if (!r.ok) throw new Error(`API ${r.status}`);
  return r.json();
}
