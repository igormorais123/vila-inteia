import { fetchBacktest } from "@/lib/api";
import Shell from "@/components/Shell";

export const dynamic = "force-dynamic";

const CYCLES: Array<[string, number, number, number, string]> = [
  ["2010", 86, 1.000, 0.060, "presidencial"],
  ["2016", 20, 0.850, 0.121, "SP municipal"],
  ["2018", 70, 1.000, 0.069, "presidencial"],
  ["2020", 30, 0.933, 0.055, "SP municipal"],
  ["2022", 120, 1.000, 0.076, "presidencial"],
  ["2024", 68, 0.735, 0.175, "SP municipal"],
];

export default async function Backtest() {
  let bt;
  try { bt = await fetchBacktest(); }
  catch (e) {
    return <Shell active="/backtest"><p className="text-red-400">{(e as Error).message}</p></Shell>;
  }
  const sweep = bt.selective_sweep || [];

  return (
    <Shell active="/backtest">
      <header className="mb-12 fade-up max-w-3xl">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Backtest histórico · year-fold cross-validation
        </div>
        <h1 className="serif text-[56px] leading-[1.05] font-light tracking-tight">
          <em className="font-normal" style={{ color: "var(--gold)" }}>94.16%</em>{" "}
          de acurácia em 6 ciclos eleitorais.
        </h1>
        <p className="text-[15px] mt-4" style={{ color: "var(--ink-2)" }}>
          394 eventos políticos brasileiros entre 2010 e 2024. Cada ciclo testado
          fora-da-amostra, treinado nos demais. Selective τ=0.15 sobe para
          96.13% em 92% de cobertura.
        </p>
      </header>

      {/* HEADLINE METRICS */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-12 fade-up"
        style={{ animationDelay: "100ms" }}>
        <Big v="394" l="eventos" sub="2010 – 2024" />
        <Big v="94.2%" l="acurácia" sub="média 6 ciclos" highlight />
        <Big v="0.089" l="brier" sub="quanto menor, melhor" />
        <Big v="100%" l="máx selective" sub="τ=0.40, 11% cobertura" />
      </section>

      {/* SELECTIVE CHART */}
      <section className="mb-16 fade-up" style={{ animationDelay: "200ms" }}>
        <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
          style={{ color: "var(--ink-3)" }}>
          Trade-off cobertura × acurácia
        </h2>
        <div className="rounded-xl p-6"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <SelectiveChart sweep={sweep} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
          <Recommend tier="τ=0.15" acc="96.1%" cov="92%"
            label="Equilibrado" desc="confiança honesta, abrangência alta" color="var(--gold)" />
          <Recommend tier="τ=0.25" acc="97.1%" cov="44%"
            label="Premium" desc="apenas calls com sinal forte" color="var(--ink-2)" />
          <Recommend tier="τ=0.40" acc="100%" cov="11%"
            label="Conservador" desc="só altíssima confiança" color="var(--pos)" />
        </div>
      </section>

      {/* CYCLES TABLE */}
      <section className="mb-12 fade-up" style={{ animationDelay: "300ms" }}>
        <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
          style={{ color: "var(--ink-3)" }}>
          Por ciclo eleitoral · year-fold CV
        </h2>
        <div className="rounded-xl overflow-hidden"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <div className="grid grid-cols-12 gap-4 px-6 py-3 text-[10px] mono uppercase tracking-[0.15em]"
            style={{ borderBottom: "1px solid var(--line)", color: "var(--ink-4)" }}>
            <div className="col-span-2">Ciclo</div>
            <div className="col-span-3">Tipo</div>
            <div className="col-span-1 text-right">n</div>
            <div className="col-span-2 text-right">Acc T≤30</div>
            <div className="col-span-2 text-right">Brier</div>
            <div className="col-span-2"></div>
          </div>
          {CYCLES.map(([year, n, acc, brier, tipo], i) => {
            const isPerf = acc === 1.0;
            const accColor = isPerf ? "var(--pos)" :
                             acc >= 0.9 ? "var(--gold)" :
                             acc >= 0.8 ? "var(--ink-2)" : "var(--neg)";
            return (
              <div key={year} className="grid grid-cols-12 gap-4 px-6 py-4 transition-colors hover:bg-white/[0.02]"
                style={{ borderBottom: i < CYCLES.length - 1 ? "1px solid var(--line)" : "none" }}>
                <div className="col-span-2 serif text-[24px] leading-none font-light tabular">
                  {year}
                </div>
                <div className="col-span-3 text-[13px] flex items-center"
                  style={{ color: "var(--ink-3)" }}>{tipo}</div>
                <div className="col-span-1 text-right text-[14px] mono tabular flex items-center justify-end"
                  style={{ color: "var(--ink-2)" }}>{n}</div>
                <div className="col-span-2 text-right mono tabular flex items-center justify-end font-semibold"
                  style={{ color: accColor, fontSize: "16px" }}>
                  {(acc * 100).toFixed(1)}%
                </div>
                <div className="col-span-2 text-right text-[13px] mono tabular flex items-center justify-end"
                  style={{ color: "var(--ink-3)" }}>
                  {brier.toFixed(3)}
                </div>
                <div className="col-span-2 flex items-center">
                  <div className="w-full h-1 rounded-full overflow-hidden"
                    style={{ background: "var(--bg-soft)" }}>
                    <div className="h-full rounded-full"
                      style={{ width: `${acc * 100}%`, background: accColor }} />
                  </div>
                </div>
              </div>
            );
          })}
          <div className="grid grid-cols-12 gap-4 px-6 py-4"
            style={{ background: "rgba(251,191,36,0.04)" }}>
            <div className="col-span-2 serif text-[20px] leading-none font-medium tabular"
              style={{ color: "var(--gold)" }}>média</div>
            <div className="col-span-3"></div>
            <div className="col-span-1 text-right mono tabular text-[14px] font-semibold flex items-center justify-end">394</div>
            <div className="col-span-2 text-right mono tabular flex items-center justify-end font-bold"
              style={{ color: "var(--gold)", fontSize: "16px" }}>94.2%</div>
            <div className="col-span-2 text-right mono tabular flex items-center justify-end font-semibold"
              style={{ color: "var(--ink-2)" }}>0.089</div>
            <div className="col-span-2"></div>
          </div>
        </div>

        <p className="text-[13px] mt-4 max-w-3xl" style={{ color: "var(--ink-3)" }}>
          <strong style={{ color: "var(--ink-2)" }}>2024 SP miss honesto.</strong>{" "}
          73.5% reflete viés sistêmico da indústria de pesquisas — Datafolha, Quaest,
          Atlas e RTBD todos com Boulos liderando, Nunes venceu por ~3pp. Modelo
          herda input dos institutos. Em corridas apertadas, use selective τ ≥ 0.25.
        </p>
      </section>
    </Shell>
  );
}

function Big({ v, l, sub, highlight = false }: { v: string; l: string; sub: string; highlight?: boolean }) {
  return (
    <div>
      <div className="text-[10px] mono uppercase tracking-[0.15em] mb-2"
        style={{ color: "var(--ink-3)" }}>{l}</div>
      <div className="serif text-[40px] leading-none font-light tabular"
        style={{ color: highlight ? "var(--gold)" : "var(--ink)" }}>
        {v}
      </div>
      <div className="text-[11px] mt-2" style={{ color: "var(--ink-4)" }}>{sub}</div>
    </div>
  );
}

function Recommend({ tier, acc, cov, label, desc, color }: {
  tier: string; acc: string; cov: string; label: string; desc: string; color: string;
}) {
  return (
    <div className="rounded-lg p-4"
      style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
      <div className="flex items-baseline justify-between">
        <span className="text-[11px] mono uppercase tracking-wider" style={{ color }}>
          {label}
        </span>
        <span className="text-[11px] mono" style={{ color: "var(--ink-4)" }}>
          {tier}
        </span>
      </div>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="serif text-[28px] leading-none font-light tabular" style={{ color }}>
          {acc}
        </span>
        <span className="text-[11px]" style={{ color: "var(--ink-4)" }}>
          em {cov} cobertura
        </span>
      </div>
      <div className="text-[12px] mt-2" style={{ color: "var(--ink-3)" }}>{desc}</div>
    </div>
  );
}

function SelectiveChart({ sweep }: { sweep: any[] }) {
  if (sweep.length === 0) return null;
  const W = 1100, H = 280, P = { l: 56, r: 24, t: 24, b: 40 };
  const pts = sweep.map((s) => ({
    x: s.coverage * 100, y: (s.acc ?? 0) * 100, tau: s.tau, n: s.n_kept,
  }));
  const yMin = 80, yMax = 102;
  const xs = (x: number) => P.l + (x / 100) * (W - P.l - P.r);
  const ys = (y: number) => H - P.b - ((y - yMin) / (yMax - yMin)) * (H - P.t - P.b);
  const path = pts.map((p, i) => `${i === 0 ? "M" : "L"} ${xs(p.x).toFixed(1)} ${ys(p.y).toFixed(1)}`).join(" ");
  // area under
  const area = path + ` L ${xs(pts[pts.length - 1].x).toFixed(1)} ${ys(yMin)} L ${xs(pts[0].x).toFixed(1)} ${ys(yMin)} Z`;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto"
      style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--gold)" stopOpacity="0.25" />
          <stop offset="100%" stopColor="var(--gold)" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* y grid */}
      {[80, 85, 90, 95, 100].map((y) => (
        <g key={y}>
          <line x1={P.l} y1={ys(y)} x2={W - P.r} y2={ys(y)}
            stroke="var(--line)" strokeDasharray="3 4" />
          <text x={P.l - 12} y={ys(y) + 4} textAnchor="end"
            fontSize="11" fontFamily="JetBrains Mono"
            fill="var(--ink-4)">{y}%</text>
        </g>
      ))}
      {/* x ticks */}
      {[0, 25, 50, 75, 100].map((x) => (
        <text key={x} x={xs(x)} y={H - P.b + 20} textAnchor="middle"
          fontSize="11" fontFamily="JetBrains Mono"
          fill="var(--ink-4)">{x}%</text>
      ))}

      {/* axis labels */}
      <text x={(W) / 2} y={H - 4} textAnchor="middle"
        fontSize="11" fontFamily="JetBrains Mono" fill="var(--ink-3)">
        Cobertura (% eventos)
      </text>
      <text x={16} y={H / 2} textAnchor="middle" transform={`rotate(-90 16 ${H / 2})`}
        fontSize="11" fontFamily="JetBrains Mono" fill="var(--ink-3)">
        Acurácia
      </text>

      {/* area */}
      <path d={area} fill="url(#grad)" />
      {/* line */}
      <path d={path} fill="none" stroke="var(--gold)" strokeWidth="2.5"
        strokeLinejoin="round" strokeLinecap="round" />

      {/* points */}
      {pts.map((p, i) => (
        <g key={i}>
          <circle cx={xs(p.x)} cy={ys(p.y)} r="5"
            fill="var(--bg-card)" stroke="var(--gold)" strokeWidth="2.5" />
          <text x={xs(p.x)} y={ys(p.y) - 14} textAnchor="middle"
            fontSize="10" fontFamily="JetBrains Mono" fill="var(--ink-3)">
            τ={p.tau.toFixed(2)}
          </text>
        </g>
      ))}
    </svg>
  );
}
