import Link from "next/link";

const links = [
  { href: "/", label: "Presidência" },
  { href: "/governadores", label: "Governadores" },
  { href: "/senado", label: "Senado" },
  { href: "/custom", label: "Predict" },
  { href: "/backtest", label: "Backtest" },
];

export default function Nav({ active }: { active: string }) {
  return (
    <nav className="flex gap-1 -mx-6 px-6"
      style={{ borderBottom: "1px solid var(--border-subtle)" }}>
      {links.map((l) => {
        const isActive = l.href === active;
        return (
          <Link
            key={l.href}
            href={l.href}
            className="px-4 py-2.5 text-[13px] font-medium transition-colors relative"
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
