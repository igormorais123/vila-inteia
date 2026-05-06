"use client";
import type { SimCandidate } from "@/lib/predict";

const REGIME_COLOR: Record<string, string> = {
  left: "#ef4444", right: "#3b82f6", center: "#94a3b8",
  pop_left: "#ec4899", pop_right: "#f97316",
};

// 2nd round: top 2 from 1st round.
// Heuristic transfer: voters of eliminated candidates split by regime affinity.
// Same regime -> 70% transfer. Adjacent (left/pop_left, right/pop_right) -> 80%.
// Opposite -> 15%. Center -> split 40/40, 20% abstain.
function regimeAffinity(from: string, to: string): number {
  if (from === to) return 0.85;
  const left = ["left", "pop_left"];
  const right = ["right", "pop_right"];
  const fLeft = left.includes(from);
  const fRight = right.includes(from);
  const tLeft = left.includes(to);
  const tRight = right.includes(to);
  if (fLeft && tLeft) return 0.80;
  if (fRight && tRight) return 0.80;
  if (from === "center") return 0.40;
  if (to === "center") return 0.30;
  return 0.15;
}

export default function SecondRound({
  candidates, winners,
}: {
  candidates: (SimCandidate & { pWinner: number })[];
  winners: number[];
}) {
  // sort by p_winner
  const sorted = [...candidates].sort((a, b) => b.pWinner - a.pWinner);
  if (sorted.length < 2) return null;
  const a = sorted[0];
  const b = sorted[1];
  const eliminated = sorted.slice(2);

  // start with 1st round shares of a and b
  let aShare = a.pWinner;
  let bShare = b.pWinner;

  // distribute eliminated shares
  for (const e of eliminated) {
    const affA = regimeAffinity(e.regime, a.regime);
    const affB = regimeAffinity(e.regime, b.regime);
    const total = affA + affB;
    if (total === 0) continue;
    aShare += e.pWinner * (affA / total) * 0.85; // 15% abstain
    bShare += e.pWinner * (affB / total) * 0.85;
  }

  // normalize
  const sum = aShare + bShare;
  const aFinal = aShare / sum;
  const bFinal = bShare / sum;

  const winner = aFinal > bFinal ? a : b;
  const margin = Math.abs(aFinal - bFinal) * 100;

  return (
    <div className="rounded-xl p-6"
      style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
      <div className="flex items-baseline justify-between mb-5">
        <span className="text-[11px] mono uppercase tracking-[0.2em]"
          style={{ color: "var(--ink-3)" }}>
          2º turno simulado
        </span>
        <span className="text-[11px]" style={{ color: "var(--ink-4)" }}>
          transferência por afinidade de regime
        </span>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-4">
        <div className={aFinal > bFinal ? "" : "opacity-60"}>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-1 h-5 rounded-sm"
              style={{ background: REGIME_COLOR[a.regime] }} />
            <span className="text-[14px] font-semibold">{a.nome}</span>
            <span className="text-[10px] mono" style={{ color: "var(--ink-3)" }}>
              {a.partido}
            </span>
          </div>
          <div className="serif text-[56px] leading-none font-light tabular"
            style={{ color: aFinal > bFinal ? "var(--gold)" : "var(--ink-2)" }}>
            {(aFinal * 100).toFixed(1)}<span className="text-[24px] opacity-50">%</span>
          </div>
        </div>
        <div className={bFinal > aFinal ? "" : "opacity-60"}>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-1 h-5 rounded-sm"
              style={{ background: REGIME_COLOR[b.regime] }} />
            <span className="text-[14px] font-semibold">{b.nome}</span>
            <span className="text-[10px] mono" style={{ color: "var(--ink-3)" }}>
              {b.partido}
            </span>
          </div>
          <div className="serif text-[56px] leading-none font-light tabular"
            style={{ color: bFinal > aFinal ? "var(--gold)" : "var(--ink-2)" }}>
            {(bFinal * 100).toFixed(1)}<span className="text-[24px] opacity-50">%</span>
          </div>
        </div>
      </div>

      <div className="flex h-4 rounded-full overflow-hidden mb-3"
        style={{ background: "var(--bg-soft)" }}>
        <div className="transition-all duration-500"
          style={{
            width: `${aFinal * 100}%`,
            background: REGIME_COLOR[a.regime],
            opacity: aFinal > bFinal ? 1 : 0.7,
          }} />
        <div className="transition-all duration-500"
          style={{
            width: `${bFinal * 100}%`,
            background: REGIME_COLOR[b.regime],
            opacity: bFinal > aFinal ? 1 : 0.7,
          }} />
      </div>

      <div className="text-[12px]" style={{ color: "var(--ink-3)" }}>
        <strong style={{ color: "var(--gold)" }}>{winner.nome}</strong> vence por{" "}
        <span className="mono">{margin.toFixed(1)}pp</span>. Eliminados:{" "}
        {eliminated.map((e) => e.nome.split(" ")[0]).join(", ") || "nenhum"}.
      </div>
    </div>
  );
}
