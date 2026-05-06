import Link from "next/link";

const links = [
  { href: "/", label: "Presidência" },
  { href: "/governadores", label: "Governadores" },
  { href: "/senado", label: "Senado" },
  { href: "/simular", label: "Simular" },
  { href: "/custom", label: "Cenário" },
  { href: "/backtest", label: "Backtest" },
];

export default function Shell({ active, children }: {
  active: string; children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <nav style={{ borderBottom: "1px solid var(--line)" }}
        className="sticky top-0 z-10"
        >
        <div className="max-w-7xl mx-auto px-8 flex items-center justify-between h-14"
          style={{ background: "rgba(12, 13, 16, 0.85)", backdropFilter: "blur(8px)" }}>
          <div className="flex items-center gap-8">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-7 h-7 rounded-md flex items-center justify-center mono text-[13px] font-bold"
                style={{
                  background: "linear-gradient(135deg, var(--gold), #d97706)",
                  color: "#000",
                }}>V</div>
              <span className="text-[14px] font-semibold tracking-tight">vila</span>
              <span className="text-[14px] font-medium" style={{ color: "var(--ink-3)" }}>
                político
              </span>
            </Link>
            <div className="flex gap-1">
              {links.map((l) => {
                const isActive = l.href === active;
                return (
                  <Link key={l.href} href={l.href}
                    className="px-3 py-1.5 text-[13px] font-medium rounded transition-colors"
                    style={{
                      color: isActive ? "var(--ink)" : "var(--ink-3)",
                      background: isActive ? "var(--bg-soft)" : "transparent",
                    }}>
                    {l.label}
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-3 text-[12px]" style={{ color: "var(--ink-3)" }}>
            <span className="mono">v1.1</span>
            <span style={{ color: "var(--line-strong)" }}>·</span>
            <span>BR 2026</span>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-8 py-10">
        {children}
      </main>
      <footer className="max-w-7xl mx-auto px-8 py-8 mt-12 text-[12px]"
        style={{ borderTop: "1px solid var(--line)", color: "var(--ink-4)" }}>
        <div className="flex justify-between">
          <span>Vila INTEIA · PC-CRD cohort + Linzer ensemble</span>
          <span className="mono">colmeia@inteia.com.br</span>
        </div>
      </footer>
    </div>
  );
}
