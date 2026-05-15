import Link from "next/link";

const links = [
  { href: "/", label: "Painel" },
  { href: "/governadores", label: "Estados" },
  { href: "/senado", label: "Senado" },
  { href: "/simular", label: "Simular" },
  { href: "/custom", label: "Cenário simples" },
  { href: "/backtest", label: "Confiança" },
];

export default function Shell({ active, children }: {
  active: string; children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <nav style={{ borderBottom: "1px solid var(--line)" }}
        className="sticky top-0 z-10"
        >
        <div className="max-w-7xl mx-auto px-4 md:px-8 flex flex-wrap md:flex-nowrap items-center justify-between min-h-14 py-2 gap-3 md:gap-5"
          style={{ background: "rgba(12, 13, 16, 0.85)", backdropFilter: "blur(8px)" }}>
          <div className="flex flex-col md:flex-row flex-1 items-start md:items-center gap-2 md:gap-8 min-w-0">
            <Link href="/" className="flex flex-shrink-0 items-center gap-2 group">
              <div className="w-7 h-7 rounded-md flex items-center justify-center mono text-[13px] font-bold"
                style={{
                  background: "linear-gradient(135deg, var(--gold), #d97706)",
                  color: "#000",
                }}>V</div>
              <span className="text-[14px] font-semibold tracking-tight whitespace-nowrap">Vila INTEIA</span>
              <span className="hidden sm:inline text-[14px] font-medium" style={{ color: "var(--ink-3)" }}>
                previsões
              </span>
            </Link>
            <div className="grid grid-cols-3 sm:flex sm:flex-wrap gap-1 min-w-0 w-full md:w-auto max-w-full">
              {links.map((l) => {
                const isActive = l.href === active;
                return (
                  <Link key={l.href} href={l.href}
                    className="px-2.5 sm:px-3 py-1.5 text-[12px] sm:text-[13px] font-medium rounded transition-colors whitespace-nowrap"
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
          <div className="hidden md:flex items-center gap-3 text-[12px] flex-shrink-0" style={{ color: "var(--ink-3)" }}>
            <span className="mono">claro</span>
            <span style={{ color: "var(--line-strong)" }}>·</span>
            <span>BR 2026</span>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 md:px-8 py-10">
        {children}
      </main>
      <footer className="max-w-7xl mx-auto px-4 md:px-8 py-8 mt-12 text-[12px]"
        style={{ borderTop: "1px solid var(--line)", color: "var(--ink-4)" }}>
        <div className="flex justify-between gap-4 flex-wrap">
          <span>Vila INTEIA - previsões políticas em português claro</span>
          <span className="mono">colmeia@inteia.com.br</span>
        </div>
      </footer>
    </div>
  );
}
