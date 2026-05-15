import Link from "next/link";

const links = [
  { href: "/", label: "Painel" },
  { href: "/governadores", label: "Estados" },
  { href: "/senado", label: "Senado" },
  { href: "/custom", label: "Cenário simples" },
  { href: "/backtest", label: "Confiança" },
];

export default function Nav({ active }: { active: string }) {
  return (
    <nav className="flex flex-wrap gap-1 -mx-6 px-6"
      style={{ borderBottom: "1px solid var(--border-subtle)" }}>
      {links.map((l) => {
        const isActive = l.href === active;
        return (
          <Link
            key={l.href}
            href={l.href}
            className="px-3 sm:px-4 py-2.5 text-[12px] sm:text-[13px] font-medium transition-colors relative whitespace-nowrap"
            style={{
              color: isActive ? "var(--amber)" : "var(--text-muted)",
              borderBottom: isActive ? "2px solid var(--amber)" : "2px solid transparent",
              marginBottom: "-1px",
            }}
          >
            {l.label}
          </Link>
        );
      })}
    </nav>
  );
}
