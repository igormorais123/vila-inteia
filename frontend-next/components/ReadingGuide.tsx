type ReadingItem = {
  label: string;
  text: string;
};

export default function ReadingGuide({
  title = "Em português claro",
  items,
}: {
  title?: string;
  items: ReadingItem[];
}) {
  return (
    <section className="rounded-xl p-5"
      style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
      <h2 className="text-[11px] mono uppercase tracking-[0.18em] mb-4"
        style={{ color: "var(--ink-3)" }}>
        {title}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {items.map((item) => (
          <div key={item.label}>
            <div className="text-[13px] font-semibold mb-1" style={{ color: "var(--ink)" }}>
              {item.label}
            </div>
            <p className="text-[12px] leading-relaxed" style={{ color: "var(--ink-3)" }}>
              {item.text}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
