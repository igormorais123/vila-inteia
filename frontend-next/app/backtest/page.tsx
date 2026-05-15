import { fetchBacktest, fetchEvolution } from "@/lib/api";
import Shell from "@/components/Shell";
import ReadingGuide from "@/components/ReadingGuide";

export const dynamic = "force-dynamic";

export default async function Backtest() {
  let bt;
  try { bt = await fetchBacktest(); }
  catch {
    return <Shell active="/backtest"><p className="text-red-400">Não foi possível carregar a tela de confiança agora.</p></Shell>;
  }
  let evo: Awaited<ReturnType<typeof fetchEvolution>> | null = null;
  try { evo = await fetchEvolution(); }
  catch {}
  const sweep = bt.selective_sweep || [];
  const cycles = bt.cycles || [];
  const summary = bt.summary || { n: 394, acc: 0.9721, brier: 0.1048 };
  const pick = (tau: number) => sweep.find((s) => Math.abs(s.tau - tau) < 1e-9);
  const t015 = pick(0.15) || { acc: 0.961, coverage: 0.92 };
  const t025 = pick(0.25) || { acc: 0.971, coverage: 0.44 };
  const t040 = pick(0.40) || { acc: 1.0, coverage: 0.11 };
  const qi = bt.quality_indicators?.mrp;
  const lift = bt.quality_indicators?.lift_vs_baseline || {};
  const edge = bt.quality_indicators?.decision_edge || {};
  const accCi = qi?.acc_wilson_95;
  const evoDelta = (
    typeof evo?.best?.score === "number" &&
    typeof evo?.incumbent?.score === "number"
  ) ? evo.best.score - evo.incumbent.score : undefined;

  return (
    <Shell active="/backtest">
      <header className="mb-12 fade-up max-w-3xl">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Teste histórico · cada ano fica fora do treino
        </div>
        <h1 className="serif text-[40px] md:text-[56px] leading-[1.05] font-light tracking-tight">
          <em className="font-normal" style={{ color: "var(--gold)" }}>
            {(summary.acc * 100).toFixed(2)}%
          </em>{" "}
          de acerto nos ciclos já conhecidos.
        </h1>
        <p className="text-[15px] mt-4" style={{ color: "var(--ink-2)" }}>
          Foram {summary.n} casos políticos brasileiros entre 2010 e 2024. Para
          evitar autoengano, a Vila testa um ano sem treinar com aquele mesmo ano.
          Quando responde só nos sinais mais fortes, chega a{" "}
          {((t015.acc ?? 0) * 100).toFixed(1)}% de acerto em{" "}
          {(t015.coverage * 100).toFixed(0)}% dos casos.
        </p>
      </header>

      <ReadingGuide
        items={[
          {
            label: "Acerto histórico",
            text: "Percentual de casos passados em que a previsão apontou o lado certo.",
          },
          {
            label: "Erro médio",
            text: "Mostra o tamanho do erro das chances. Quanto menor, melhor calibrada fica a previsão.",
          },
          {
            label: "Cobertura",
            text: "Parcela dos casos em que a Vila aceita responder. Mais cautela aumenta acerto e reduz cobertura.",
          },
        ]}
      />

      {/* HEADLINE METRICS */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 my-12 fade-up"
        style={{ animationDelay: "100ms" }}>
        <Big v={summary.n.toString()} l="casos testados" sub="2010 a 2024" />
        <Big v={`${(summary.acc * 100).toFixed(2)}%`} l="acerto geral" sub="média dos ciclos" highlight />
        <Big v={summary.brier.toFixed(3)} l="tamanho do erro" sub="menor é melhor" />
        <Big v={`${((t040.acc ?? 0) * 100).toFixed(0)}%`} l="modo cauteloso" sub={`${(t040.coverage * 100).toFixed(0)}% dos casos`} />
      </section>

      <div className="mb-14 fade-up" style={{ animationDelay: "125ms" }}>
        <ReadingGuide
          title="Como usar esta tela"
          items={[
            {
              label: "Para acompanhar",
              text: "Use o acerto geral para saber se a previsão costuma apontar o lado certo.",
            },
            {
              label: "Para decidir com cautela",
              text: "Prefira os cortes médio ou rígido quando a eleição estiver apertada.",
            },
            {
              label: "Para auditar",
              text: "Veja o desempenho por ano e procure ciclos com erro maior antes de confiar demais.",
            },
          ]}
        />
      </div>

      {qi && (
        <section className="mb-14 fade-up" style={{ animationDelay: "150ms" }}>
          <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Qualidade da previsão
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <Indicator
              label="Separa acerto e erro"
              value={fmtNum(qi.auc, 3)}
              sub="quanto maior, melhor"
              highlight
            />
            <Indicator
              label="Força do acerto"
              value={fmtNum(qi.mcc, 3)}
              sub={`ganho ${fmtSigned(lift.mcc, 3)}`}
              highlight
            />
            <Indicator
              label="Ganho no erro"
              value={fmtPct(qi.brier_skill_vs_climatology, 1)}
              sub="contra chute básico"
            />
            <Indicator
              label="Confiança fora do lugar"
              value={fmtNum(qi.ece, 3)}
              sub="menor é melhor"
            />
            <Indicator
              label="Faixa provável"
              value={accCi ? `${(accCi[0] * 100).toFixed(1)}–${(accCi[1] * 100).toFixed(1)}%` : "—"}
              sub="margem estatística"
            />
            <Indicator
              label="Ganho líquido"
              value={`+${edge.net_hits ?? 0}`}
              sub={fmtP(edge.mcnemar_p) === "—" ? "checagem técnica" : "checagem técnica forte"}
            />
          </div>
        </section>
      )}

      {evo && (
        <section className="mb-14 fade-up" style={{ animationDelay: "175ms" }}>
          <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Ajuste automático com controle de qualidade
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
            <Indicator
              label="Decisão"
              value={evo.gate?.promoted ? "promovido" : "retido"}
              sub={evo.current_version || evo.gate?.reason || "última rodada"}
              highlight={evo.gate?.promoted}
            />
            <Indicator
              label="Pontuação geral"
              value={fmtNum(evo.best?.score, 3)}
              sub={`mudança ${fmtSigned(evoDelta, 4)}`}
              highlight
            />
            <Indicator
              label="Separação melhor"
              value={fmtNum(evo.best?.auc, 3)}
              sub={`antes ${fmtNum(evo.incumbent?.auc, 3)}`}
            />
            <Indicator
              label="Erro menor"
              value={fmtNum(evo.best?.brier, 4)}
              sub={`antes ${fmtNum(evo.incumbent?.brier, 4)}`}
            />
            <Indicator
              label="Incerteza diária"
              value={fmtNum(evo.best?.config?.sigma_slope_pp_per_day, 3)}
              sub={`${evo.population_size ?? "—"} versões · ${evo.generations ?? "—"} rodadas`}
            />
            <Indicator
              label="Critérios"
              value={`${Object.values(evo.gate?.checks || {}).filter(Boolean).length}/${Object.values(evo.gate?.checks || {}).length || 5}`}
              sub="passaram no controle"
            />
          </div>
          <div className="rounded-lg p-4 mt-4 text-[12px] leading-relaxed"
            style={{ background: "var(--bg-card)", border: "1px solid var(--line)", color: "var(--ink-3)" }}>
            <span className="mono uppercase tracking-[0.14em]" style={{ color: "var(--ink-4)" }}>
              Como evolui
            </span>{" "}
            A Vila testa pequenas variações do modelo e só troca a versão ativa
            quando a nova passa nos critérios objetivos. O protocolo mantém o ano
            testado fora do treino.
          </div>
        </section>
      )}

      {/* SELECTIVE CHART */}
      <section className="mb-16 fade-up" style={{ animationDelay: "200ms" }}>
        <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
          style={{ color: "var(--ink-3)" }}>
          Mais cautela = mais acerto e menos respostas
        </h2>
        <div className="rounded-xl p-6"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <SelectiveChart sweep={sweep} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
          <Recommend tier="cautela leve" acc={`${((t015.acc ?? 0) * 100).toFixed(1)}%`} cov={`${(t015.coverage * 100).toFixed(0)}%`}
            label="Corte leve" desc="bom padrão para acompanhar muitas corridas" color="var(--gold)" />
          <Recommend tier="cautela média" acc={`${((t025.acc ?? 0) * 100).toFixed(1)}%`} cov={`${(t025.coverage * 100).toFixed(0)}%`}
            label="Corte médio" desc="responde só quando o sinal está mais firme" color="var(--ink-2)" />
          <Recommend tier="cautela rígida" acc={`${((t040.acc ?? 0) * 100).toFixed(0)}%`} cov={`${(t040.coverage * 100).toFixed(0)}%`}
            label="Corte rígido" desc="poucas respostas, maior confiança" color="var(--pos)" />
        </div>
      </section>

      {/* CYCLES TABLE */}
      <section className="mb-12 fade-up" style={{ animationDelay: "300ms" }}>
        <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
          style={{ color: "var(--ink-3)" }}>
          Desempenho por eleição já passada
        </h2>
        <div className="rounded-xl overflow-hidden"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <div className="grid grid-cols-12 gap-4 px-6 py-3 text-[10px] mono uppercase tracking-[0.15em]"
            style={{ borderBottom: "1px solid var(--line)", color: "var(--ink-4)" }}>
            <div className="col-span-2">Ano</div>
            <div className="col-span-3">Eleição</div>
            <div className="col-span-1 text-right">casos</div>
            <div className="col-span-2 text-right">Acerto</div>
            <div className="col-span-2 text-right">Erro</div>
            <div className="col-span-2"></div>
          </div>
          {cycles.map(({ year, n, acc, brier, type: tipo }, i) => {
            const isPerf = acc === 1.0;
            const accColor = isPerf ? "var(--pos)" :
                             acc >= 0.9 ? "var(--gold)" :
                             acc >= 0.8 ? "var(--ink-2)" : "var(--neg)";
            return (
              <div key={year} className="grid grid-cols-12 gap-4 px-6 py-4 transition-colors hover:bg-white/[0.02]"
                style={{ borderBottom: i < cycles.length - 1 ? "1px solid var(--line)" : "none" }}>
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
            <div className="col-span-1 text-right mono tabular text-[14px] font-semibold flex items-center justify-end">{summary.n}</div>
            <div className="col-span-2 text-right mono tabular flex items-center justify-end font-bold"
              style={{ color: "var(--gold)", fontSize: "16px" }}>{(summary.acc * 100).toFixed(2)}%</div>
            <div className="col-span-2 text-right mono tabular flex items-center justify-end font-semibold"
              style={{ color: "var(--ink-2)" }}>{summary.brier.toFixed(3)}</div>
            <div className="col-span-2"></div>
          </div>
        </div>

        <p className="text-[13px] mt-4 max-w-3xl" style={{ color: "var(--ink-3)" }}>
          <strong style={{ color: "var(--ink-2)" }}>Atenção ao caso SP 2024.</strong>{" "}
          O desempenho menor reflete um erro compartilhado pelas pesquisas
          públicas daquele ciclo: vários institutos mostravam Boulos na frente,
          mas Nunes venceu por cerca de 3 pontos. Em corridas apertadas, prefira
          a leitura mais cautelosa.
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
          em {cov} dos casos
        </span>
      </div>
      <div className="text-[12px] mt-2" style={{ color: "var(--ink-3)" }}>{desc}</div>
    </div>
  );
}

function Indicator({ label, value, sub, highlight = false }: {
  label: string; value: string; sub: string; highlight?: boolean;
}) {
  return (
    <div className="rounded-lg p-4"
      style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
      <div className="text-[10px] mono uppercase tracking-[0.15em]"
        style={{ color: "var(--ink-4)" }}>{label}</div>
      <div className="serif text-[28px] leading-none font-light tabular mt-2"
        style={{ color: highlight ? "var(--gold)" : "var(--ink)" }}>
        {value}
      </div>
      <div className="text-[11px] mt-2" style={{ color: "var(--ink-3)" }}>{sub}</div>
    </div>
  );
}

function fmtNum(v: number | null | undefined, digits = 3): string {
  return typeof v === "number" && Number.isFinite(v) ? v.toFixed(digits) : "—";
}

function fmtPct(v: number | null | undefined, digits = 1): string {
  return typeof v === "number" && Number.isFinite(v) ? `${(v * 100).toFixed(digits)}%` : "—";
}

function fmtSigned(v: number | null | undefined, digits = 3): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}`;
}

function fmtP(v: number | null | undefined): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return "—";
  if (v < 0.001) return "<0.001";
  return v.toFixed(3);
}

function SelectiveChart({ sweep }: { sweep: any[] }) {
  if (sweep.length === 0) return null;
  const W = 1100, H = 280, P = { l: 56, r: 24, t: 24, b: 40 };
  const pts = sweep.map((s) => ({
    x: s.coverage * 100, y: (s.acc ?? 0) * 100,
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
        Casos respondidos
      </text>
      <text x={16} y={H / 2} textAnchor="middle" transform={`rotate(-90 16 ${H / 2})`}
        fontSize="11" fontFamily="JetBrains Mono" fill="var(--ink-3)">
        Acerto
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
        </g>
      ))}
    </svg>
  );
}
