import { clsx } from "clsx";

const PARTY_COLORS: Record<string, string> = {
  PT: "#cc1f1a", PSOL: "#ec1c24", PCdoB: "#cc1f1a", PSB: "#fbbf24",
  PDT: "#dc2626", REDE: "#16a34a",
  PL: "#1d4ed8", PSD: "#1d4ed8", REPUB: "#1d4ed8", REP: "#1d4ed8",
  UNIAO: "#1e40af", PP: "#dc2626", PSDB: "#0ea5e9", MDB: "#16a34a",
  NOVO: "#fb923c", PODE: "#7c3aed", CIDADANIA: "#fb923c",
};

const REGIME_LABEL: Record<string, string> = {
  left: "esquerda", right: "direita", center: "centro",
  pop_left: "pop. esquerda", pop_right: "pop. direita",
};

export function PartyBadge({ partido }: { partido: string }) {
  const color = PARTY_COLORS[partido] || "#6b6b75";
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold tracking-wide"
      style={{ background: `${color}22`, color, border: `1px solid ${color}55` }}
    >
      {partido}
    </span>
  );
}

export function RegimeBadge({ regime }: { regime: string }) {
  const v = `var(--regime-${regime})`;
  const label = REGIME_LABEL[regime] || regime;
  return (
    <span
      className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono"
      style={{ background: `${v}1a`, color: v, border: `1px solid ${v}33` }}
    >
      {label}
    </span>
  );
}

export function StatusBadge({ status }: { status?: string }) {
  if (!status || status === "speculation") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono"
        style={{ background: "rgba(161,161,170,0.1)", color: "var(--text-muted)",
                 border: "1px solid rgba(161,161,170,0.2)" }}>
        especulação
      </span>
    );
  }
  if (status === "ineligible") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono"
        style={{ background: "rgba(239,68,68,0.12)", color: "#f87171",
                 border: "1px solid rgba(239,68,68,0.3)" }}>
        inelegível
      </span>
    );
  }
  if (status === "confirmed") {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono"
        style={{ background: "rgba(34,197,94,0.12)", color: "#4ade80",
                 border: "1px solid rgba(34,197,94,0.3)" }}>
        confirmado
      </span>
    );
  }
  return null;
}

export function IncumbBadge({ incumb }: { incumb?: number }) {
  if (incumb === 1) {
    return (
      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide"
        style={{ background: "rgba(245,165,36,0.1)", color: "var(--amber)",
                 border: "1px solid rgba(245,165,36,0.25)" }}>
        incumb.
      </span>
    );
  }
  return null;
}
