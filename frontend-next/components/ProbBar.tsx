interface Props {
  value: number;
  label?: React.ReactNode;
  highlight?: boolean;
  height?: number;
  showValue?: boolean;
  rightLabel?: string;
}

export default function ProbBar({
  value, label, highlight = false, height = 8, showValue = true, rightLabel,
}: Props) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const barColor = highlight ? "var(--amber)" : "var(--amber-dim)";

  return (
    <div className="flex items-center gap-3 py-1">
      {label && (
        <span className="text-sm flex-shrink-0 min-w-[200px]"
          style={{ color: "var(--text-secondary)" }}>{label}</span>
      )}
      <div
        className="flex-1 rounded-full overflow-hidden relative"
        style={{ background: "var(--bg-elevated)", height: `${height}px` }}
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            background: highlight
              ? `linear-gradient(90deg, ${barColor}, var(--amber))`
              : barColor,
          }}
        />
      </div>
      {showValue && (
        <span
          className="font-mono text-sm tabular w-16 text-right flex-shrink-0"
          style={{ color: highlight ? "var(--amber)" : "var(--text-primary)" }}
        >
          {pct.toFixed(1)}%
        </span>
      )}
      {rightLabel && (
        <span className="text-xs font-mono flex-shrink-0"
          style={{ color: "var(--text-muted)" }}>{rightLabel}</span>
      )}
    </div>
  );
}
