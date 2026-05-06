export default function Disclaimer({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="rounded-lg p-3 text-[13px] leading-relaxed flex items-start gap-2.5"
      style={{
        background: "rgba(245, 165, 36, 0.06)",
        border: "1px solid rgba(245, 165, 36, 0.18)",
        color: "rgba(245, 200, 130, 0.95)",
      }}
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="2" className="flex-shrink-0 mt-0.5">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <div>{children}</div>
    </div>
  );
}
