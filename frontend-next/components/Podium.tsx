import { PartyBadge } from "./Badge";
import type { Candidate } from "@/lib/api";

export default function Podium({ candidates }: { candidates: Candidate[] }) {
  if (candidates.length < 3) return null;
  const [first, second, third] = candidates;

  const tile = (c: Candidate, rank: 1 | 2 | 3) => {
    const sizes = {
      1: { ring: "ring-2 ring-amber-500/40", scale: "scale-105", bg: "rgba(245, 165, 36, 0.08)" },
      2: { ring: "", scale: "", bg: "var(--bg-surface)" },
      3: { ring: "", scale: "", bg: "var(--bg-surface)" },
    };
    const p = (c.p_winner ?? 0) * 100;
    const accent = rank === 1 ? "var(--amber)" : "var(--text-secondary)";
    return (
      <div
        className={`flex flex-col rounded-xl border p-4 transition-transform ${sizes[rank].scale}`}
        style={{
          background: sizes[rank].bg,
          borderColor: rank === 1 ? "rgba(245,165,36,0.35)" : "var(--border-subtle)",
          boxShadow: rank === 1 ? "0 8px 32px rgba(245,165,36,0.12)" : "none",
        }}
      >
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-[11px] uppercase tracking-wider"
            style={{ color: "var(--text-muted)" }}>
            #{rank}
          </span>
          <PartyBadge partido={c.partido} />
        </div>
        <div className="text-[15px] font-semibold leading-tight mb-1">
          {c.nome.split(" ").slice(0, -1).join(" ")}
          <br />
          <span className="font-bold">{c.nome.split(" ").slice(-1)}</span>
        </div>
        <div className="mt-auto pt-3">
          <div className="font-mono text-[28px] font-bold tabular leading-none"
            style={{ color: accent }}>
            {p.toFixed(1)}<span className="text-[18px] opacity-60">%</span>
          </div>
          <div className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>
            P(vencer) · {c.regime}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="grid grid-cols-3 gap-3">
      {tile(first, 1)}
      {tile(second, 2)}
      {tile(third, 3)}
    </div>
  );
}
