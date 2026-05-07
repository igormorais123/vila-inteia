import { PartyBadge, RegimeBadge, IncumbBadge } from "./Badge";
import type { Candidate } from "@/lib/api";

interface Props {
  candidate: Candidate;
  rank?: number;
  highlight?: boolean;
  showStatus?: boolean;
}

export default function CandidateRow({
  candidate, rank, highlight = false, showStatus = false,
}: Props) {
  const c = candidate;
  const p = c.p_winner ?? c.p_raw ?? 0;
  const pct = p * 100;

  return (
    <div
      className="flex items-center gap-4 py-3 px-3 rounded-lg transition-colors"
      style={{
        background: highlight ? "rgba(245, 165, 36, 0.04)" : "transparent",
        borderLeft: highlight ? "2px solid var(--amber)" : "2px solid transparent",
      }}
    >
      {rank !== undefined && (
        <span
          className="font-mono text-xs tabular w-6 flex-shrink-0 text-center"
          style={{ color: "var(--text-muted)" }}
        >
          {rank.toString().padStart(2, "0")}
        </span>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[14px] font-medium truncate"
            style={{ color: "var(--text-primary)" }}>
            {c.nome}
          </span>
          <PartyBadge partido={c.partido} />
          {c.regime && <RegimeBadge regime={c.regime} />}
          {c.incumbente !== undefined && <IncumbBadge incumb={c.incumbente} />}
        </div>
        {showStatus && c.status_note && (
          <p className="text-[11px] mt-1" style={{ color: "var(--text-muted)" }}>
            {c.status_note}
          </p>
        )}
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        <div
          className="rounded-full overflow-hidden"
          style={{
            width: "120px", height: "6px", background: "var(--bg-elevated)",
          }}
        >
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${pct}%`,
              background: highlight
                ? "linear-gradient(90deg, var(--amber-dim), var(--amber))"
                : "var(--amber-dim)",
            }}
          />
        </div>
        <span
          className="font-mono text-sm tabular w-14 text-right"
          style={{ color: highlight ? "var(--amber)" : "var(--text-primary)" }}
        >
          {pct.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
