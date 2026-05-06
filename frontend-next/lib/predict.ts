// Client-side replica of cohort + Linzer ensemble.
// Mirrors engine/political_cohort.py + scripts/predict_2026.py.
// Lets simulator run instantly without per-candidate API roundtrip.

export const W_LINZER = 0.5;
export const W_COHORT = 0.5;
export const SIGMA_INT = 4.0;
export const SIGMA_SLOPE = 0.05;

// erf approximation (Abramowitz & Stegun 7.1.26)
function erf(x: number): number {
  const sign = x < 0 ? -1 : 1;
  x = Math.abs(x);
  const a1 =  0.254829592;
  const a2 = -0.284496736;
  const a3 =  1.421413741;
  const a4 = -1.453152027;
  const a5 =  1.061405429;
  const p  =  0.3275911;
  const t = 1.0 / (1.0 + p * x);
  const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
  return sign * y;
}

export function leadToPLinzer(leadPp: number, daysToElection: number): number {
  const sigma = SIGMA_INT + SIGMA_SLOPE * Math.max(0, daysToElection);
  const z = leadPp / Math.max(sigma, 1.0);
  return 0.5 * (1.0 + erf(z / Math.sqrt(2.0)));
}

// Approximation of cohort prior — falls back to global rate ~0.78 with
// Stein shrinkage to 0.5 for unknown cohorts. Real model has full table,
// but for simulator UX this approximation is fine.
const GLOBAL_RATE = 0.78;
const SHRINK = 0.05;

export function pCohortApprox(incumbente: number, regime: string, leadPp: number): number {
  // crude proxy: global rate * incumbency boost * regime adjust
  let p = GLOBAL_RATE;
  if (incumbente === 0) p *= 0.92;
  if (regime === "pop_left" || regime === "pop_right") p *= 0.85;
  if (regime === "left" && leadPp > 0) p *= 1.05;
  // shrink to 0.5
  return Math.min(0.99, Math.max(0.01, (1 - SHRINK) * p + SHRINK * 0.5));
}

export interface SimCandidate {
  id: string;
  nome: string;
  partido: string;
  regime: string;
  incumbente: number;
  leadPp: number;
}

export function predictBlend(c: SimCandidate, days: number): {
  pCohort: number; pLinzer: number; pBlend: number;
} {
  const pCohort = pCohortApprox(c.incumbente, c.regime, c.leadPp);
  const pLinzer = leadToPLinzer(c.leadPp, days);
  const pBlend = W_COHORT * pCohort + W_LINZER * pLinzer;
  return { pCohort, pLinzer, pBlend };
}

export function normalize(probs: number[]): number[] {
  const s = probs.reduce((a, b) => a + Math.max(0.001, b), 0);
  return probs.map((p) => Math.max(0.001, p) / s);
}
