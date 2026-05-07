"use client";
import { predictBlend, normalize, type SimCandidate } from "@/lib/predict";

const REGIME_COLOR: Record<string, string> = {
  left: "#ef4444", right: "#3b82f6", center: "#94a3b8",
  pop_left: "#ec4899", pop_right: "#f97316",
};

export default function Trajectory({
  candidates, currentDays,
}: {
  candidates: SimCandidate[];
  currentDays: number;
}) {
  if (candidates.length === 0) return null;

  // sample days from 365 down to 0
  const steps = 60;
  const xs = Array.from({ length: steps + 1 }, (_, i) => 365 - (i / steps) * 365);

  // for each x (days), compute normalized winner probs
  const trajectories: Record<string, { x: number; y: number }[]> = {};
  candidates.forEach((c) => { trajectories[c.id] = []; });

  xs.forEach((d) => {
    const blends = candidates.map((c) => predictBlend(c, d).pBlend);
    const winners = normalize(blends);
    candidates.forEach((c, i) => {
      trajectories[c.id].push({ x: d, y: winners[i] });
    });
  });

  const W = 1100, H = 280, P = { l: 56, r: 100, t: 24, b: 40 };
  const xMin = 0, xMax = 365;
  // y range adapts to actual values
  const allY = Object.values(trajectories).flatMap((arr) => arr.map((p) => p.y));
  const yMax = Math.min(1, Math.max(0.5, Math.max(...allY) * 1.1));
  const yMin = Math.max(0, Math.min(...allY) * 0.85);

  // x axis: 365 -> 0 left to right (time progresses to election)
  const xs_ = (x: number) => P.l + ((xMax - x) / (xMax - xMin)) * (W - P.l - P.r);
  const ys_ = (y: number) => H - P.b - ((y - yMin) / (yMax - yMin)) * (H - P.t - P.b);

  // sort candidates by current p (ascending so leader drawn last/on top)
  const ordered = [...candidates].sort((a, b) => {
    const pa = trajectories[a.id].find((p) => Math.abs(p.x - currentDays) < 4)?.y ?? 0;
    const pb = trajectories[b.id].find((p) => Math.abs(p.x - currentDays) < 4)?.y ?? 0;
    return pa - pb;
  });

  return (
    <div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
        {/* y grid */}
        {[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
          .filter((y) => y >= yMin && y <= yMax)
          .map((y) => (
            <g key={y}>
              <line x1={P.l} y1={ys_(y)} x2={W - P.r} y2={ys_(y)}
                stroke="var(--line)" strokeDasharray="3 4" />
              <text x={P.l - 12} y={ys_(y) + 4} textAnchor="end"
                fontSize="11" fontFamily="JetBrains Mono"
                fill="var(--ink-4)">{(y * 100).toFixed(0)}%</text>
            </g>
          ))}

        {/* x ticks */}
        {[365, 270, 180, 90, 30, 0].map((d) => (
          <g key={d}>
            <line x1={xs_(d)} y1={H - P.b} x2={xs_(d)} y2={H - P.b + 4}
              stroke="var(--line-strong)" />
            <text x={xs_(d)} y={H - P.b + 18} textAnchor="middle"
              fontSize="11" fontFamily="JetBrains Mono"
              fill="var(--ink-4)">{d}d</text>
          </g>
        ))}

        {/* current days marker */}
        <line x1={xs_(currentDays)} y1={P.t} x2={xs_(currentDays)} y2={H - P.b}
          stroke="var(--gold)" strokeWidth="1" strokeDasharray="2 4" opacity="0.8" />
        <text x={xs_(currentDays)} y={P.t - 6} textAnchor="middle"
          fontSize="10" fontFamily="JetBrains Mono" fill="var(--gold)">
          hoje · {currentDays}d
        </text>

        {/* axis labels */}
        <text x={P.l + (W - P.l - P.r) / 2} y={H - 4} textAnchor="middle"
          fontSize="11" fontFamily="JetBrains Mono" fill="var(--ink-3)">
          ← longe ·  dias até eleição  · perto →
        </text>

        {/* lines */}
        {ordered.map((c) => {
          const color = REGIME_COLOR[c.regime] || "#94a3b8";
          const path = trajectories[c.id]
            .map((p, i) => `${i === 0 ? "M" : "L"} ${xs_(p.x).toFixed(1)} ${ys_(p.y).toFixed(1)}`)
            .join(" ");
          const last = trajectories[c.id][trajectories[c.id].length - 1];
          return (
            <g key={c.id}>
              <path d={path} fill="none" stroke={color} strokeWidth="2"
                strokeLinejoin="round" strokeLinecap="round" />
              {/* end label */}
              <circle cx={xs_(last.x)} cy={ys_(last.y)} r="3" fill={color} />
              <text x={xs_(last.x) + 8} y={ys_(last.y) + 4}
                fontSize="11" fontFamily="JetBrains Mono" fill={color}
                style={{ fontWeight: 500 }}>
                {c.nome.split(" ")[0]} · {(last.y * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}

        {/* current point dots */}
        {candidates.map((c) => {
          const pt = trajectories[c.id].find((p) => Math.abs(p.x - currentDays) < 4);
          if (!pt) return null;
          const color = REGIME_COLOR[c.regime] || "#94a3b8";
          return (
            <circle key={c.id} cx={xs_(pt.x)} cy={ys_(pt.y)} r="5"
              fill="var(--bg-card)" stroke={color} strokeWidth="2.5" />
          );
        })}
      </svg>
    </div>
  );
}
