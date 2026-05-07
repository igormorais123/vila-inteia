interface Props {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}

export default function Header({ title, subtitle, right }: Props) {
  return (
    <header className="bg-radial-amber -mx-6 -mt-6 px-6 pt-6 pb-3">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center font-mono text-sm font-bold"
            style={{
              background: "linear-gradient(135deg, var(--amber) 0%, #d97706 100%)",
              color: "#0a0a0c",
              boxShadow: "0 4px 12px rgba(245,165,36,0.25)",
            }}
          >
            V
          </div>
          <div>
            <h1 className="text-[22px] font-semibold leading-tight tracking-tight">
              {title}
            </h1>
            {subtitle && (
              <p className="text-[13px] mt-0.5"
                style={{ color: "var(--text-muted)" }}>
                {subtitle}
              </p>
            )}
          </div>
        </div>
        {right && <div className="flex-shrink-0">{right}</div>}
      </div>
    </header>
  );
}
