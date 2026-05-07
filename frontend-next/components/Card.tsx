import { clsx } from "clsx";

export function Card({ children, className, padded = true }: {
  children: React.ReactNode; className?: string; padded?: boolean;
}) {
  return (
    <div
      className={clsx(
        "rounded-xl border transition-colors",
        padded && "p-5",
        className,
      )}
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border-subtle)",
      }}
    >
      {children}
    </div>
  );
}

export function StatCard({ label, value, sub, accent = false }: {
  label: string; value: string | number; sub?: string; accent?: boolean;
}) {
  return (
    <Card>
      <div className="text-[10px] uppercase tracking-[0.12em] font-mono"
        style={{ color: "var(--text-muted)" }}>{label}</div>
      <div
        className="text-3xl font-mono font-semibold mt-2 tabular leading-none"
        style={{ color: accent ? "var(--amber)" : "var(--text-primary)" }}
      >
        {value}
      </div>
      {sub && (
        <div className="text-xs mt-2 leading-relaxed"
          style={{ color: "var(--text-muted)" }}>{sub}</div>
      )}
    </Card>
  );
}

export function SectionTitle({ children, sub }: { children: React.ReactNode; sub?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-xs font-semibold uppercase tracking-[0.15em] font-mono"
        style={{ color: "var(--text-secondary)" }}>{children}</h2>
      {sub && <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{sub}</p>}
    </div>
  );
}
