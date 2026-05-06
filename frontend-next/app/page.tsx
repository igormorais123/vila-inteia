import { fetchPresidente, fetchHealth } from "@/lib/api";
import Shell from "@/components/Shell";

export const dynamic = "force-dynamic";

const REGIME_LABEL: Record<string, string> = {
  left: "esquerda", right: "direita", center: "centro",
  pop_left: "pop. esq", pop_right: "pop. dir",
};

const REGIME_COLOR: Record<string, string> = {
  left: "var(--left)", right: "var(--right)", center: "var(--center)",
  pop_left: "var(--pop-left)", pop_right: "var(--pop-right)",
};

export default async function Home() {
  let snap, health;
  try { [snap, health] = await Promise.all([fetchPresidente(), fetchHealth()]); }
  catch (e) {
    return <Shell active="/"><p className="text-red-400">API: {(e as Error).message}</p></Shell>;
  }

  const sorted = [...snap.candidates].sort((a, b) => (b.p_winner ?? 0) - (a.p_winner ?? 0));
  const leader = sorted[0];
  const runner = sorted[1];
  const lead = ((leader.p_winner ?? 0) - (runner.p_winner ?? 0)) * 100;

  const totalLeft = sorted.filter((c) => c.regime?.includes("left"))
    .reduce((s, c) => s + (c.p_winner ?? 0), 0);
  const totalRight = sorted.filter((c) => c.regime?.includes("right"))
    .reduce((s, c) => s + (c.p_winner ?? 0), 0);
  const totalCenter = sorted.filter((c) => c.regime === "center")
    .reduce((s, c) => s + (c.p_winner ?? 0), 0);

  return (
    <Shell active="/">
      {/* HERO */}
      <section className="grid grid-cols-12 gap-8 mb-16 fade-up">
        <div className="col-span-12 lg:col-span-7">
          <div className="text-[11px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Presidência da República · 1º turno · {snap.horizon_days} dias
          </div>
          <h1 className="serif text-[68px] leading-[1.05] font-light tracking-tight mb-4">
            Lula lidera, mas <em className="font-normal" style={{ color: "var(--gold)" }}>
            corrida fragmentada</em>{" "}
            entre 5 nomes.
          </h1>
          <p className="text-[16px] leading-relaxed max-w-2xl"
            style={{ color: "var(--ink-2)" }}>
            Modelo Vila aponta {((leader.p_winner ?? 0) * 100).toFixed(1)}% de
            probabilidade para {leader.nome.split(" ").slice(-1)} contra{" "}
            {((runner.p_winner ?? 0) * 100).toFixed(1)}% de {runner.nome.split(" ")[0]} {runner.nome.split(" ").slice(-1)}.
            A direita unificada (Tarcísio + Ratinho + Zema){" "}
            soma <span className="font-semibold" style={{ color: "var(--ink)" }}>
            {(totalRight * 100).toFixed(1)}%</span>, mais que o líder isolado.
          </p>
        </div>

        <div className="col-span-12 lg:col-span-5 flex items-center">
          <div className="w-full">
            <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
              style={{ color: "var(--ink-3)" }}>
              Líder no momento
            </div>
            <div className="flex items-baseline gap-3">
              <span className="serif text-[140px] leading-none font-light tabular"
                style={{ color: "var(--gold)" }}>
                {((leader.p_winner ?? 0) * 100).toFixed(1)}
              </span>
              <span className="serif text-[48px] font-light"
                style={{ color: "var(--gold)" }}>%</span>
            </div>
            <div className="text-[20px] font-semibold mt-2">{leader.nome}</div>
            <div className="text-[13px] mt-1" style={{ color: "var(--ink-3)" }}>
              {leader.partido} · {REGIME_LABEL[leader.regime || "center"]} · incumbente
            </div>
            <div className="mt-4 inline-flex items-center gap-1.5 px-2 py-1 rounded text-[12px] mono"
              style={{ background: "var(--bg-soft)", color: "var(--ink-2)" }}>
              <span style={{ color: "var(--pos)" }}>+{lead.toFixed(1)}pp</span>
              <span style={{ color: "var(--ink-4)" }}>vs 2º</span>
            </div>
          </div>
        </div>
      </section>

      {/* DISTRIBUTION BAR */}
      <section className="mb-16 fade-up" style={{ animationDelay: "100ms" }}>
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-[12px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Distribuição de probabilidade
          </h2>
          <span className="text-[11px] mono" style={{ color: "var(--ink-4)" }}>
            soma = 100%
          </span>
        </div>

        <div className="flex h-12 rounded overflow-hidden"
          style={{ border: "1px solid var(--line)" }}>
          {sorted.map((c, i) => {
            const pct = (c.p_winner ?? 0) * 100;
            const color = REGIME_COLOR[c.regime || "center"];
            return (
              <div key={c.nome}
                className="relative group transition-all"
                style={{
                  width: `${pct}%`,
                  background: color,
                  borderRight: i < sorted.length - 1 ? "1px solid var(--bg)" : "none",
                  opacity: i === 0 ? 1 : 0.7,
                }}>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-[11px] font-semibold mono tabular text-black/80">
                    {pct >= 12 ? `${pct.toFixed(1)}%` : ""}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="grid grid-cols-5 gap-2 mt-3">
          {sorted.map((c) => {
            const pct = (c.p_winner ?? 0) * 100;
            const color = REGIME_COLOR[c.regime || "center"];
            return (
              <div key={c.nome} className="flex items-start gap-2">
                <div className="w-1 self-stretch rounded-sm flex-shrink-0 mt-0.5"
                  style={{ background: color }} />
                <div className="min-w-0">
                  <div className="text-[12px] font-medium truncate">
                    {c.nome.split(" ").slice(-1)[0]}
                  </div>
                  <div className="text-[10px] mono" style={{ color: "var(--ink-3)" }}>
                    {c.partido} · {pct.toFixed(1)}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* HEAD TO HEAD */}
      <section className="grid grid-cols-12 gap-6 mb-16 fade-up" style={{ animationDelay: "200ms" }}>
        <div className="col-span-12 md:col-span-7 rounded-xl p-6"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <div className="text-[11px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Esquerda vs Direita unificada
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <div className="text-[12px] uppercase tracking-wider mb-1"
                style={{ color: "var(--left)" }}>
                Esquerda
              </div>
              <div className="serif text-[56px] leading-none tabular font-light"
                style={{ color: "var(--ink)" }}>
                {(totalLeft * 100).toFixed(1)}<span className="text-[24px] opacity-50">%</span>
              </div>
              <div className="text-[12px] mt-2" style={{ color: "var(--ink-3)" }}>
                Lula + Boulos
              </div>
            </div>
            <div>
              <div className="text-[12px] uppercase tracking-wider mb-1"
                style={{ color: "var(--right)" }}>
                Direita unificada
              </div>
              <div className="serif text-[56px] leading-none tabular font-light"
                style={{ color: "var(--ink)" }}>
                {(totalRight * 100).toFixed(1)}<span className="text-[24px] opacity-50">%</span>
              </div>
              <div className="text-[12px] mt-2" style={{ color: "var(--ink-3)" }}>
                Tarcísio + Ratinho + Zema
              </div>
            </div>
          </div>
          <div className="mt-6 flex h-2 rounded-full overflow-hidden"
            style={{ background: "var(--bg-soft)" }}>
            <div style={{
              width: `${(totalLeft / (totalLeft + totalRight + totalCenter || 1)) * 100}%`,
              background: "var(--left)",
            }} />
            <div style={{
              width: `${(totalCenter / (totalLeft + totalRight + totalCenter || 1)) * 100}%`,
              background: "var(--center)",
            }} />
            <div style={{
              width: `${(totalRight / (totalLeft + totalRight + totalCenter || 1)) * 100}%`,
              background: "var(--right)",
            }} />
          </div>
          <div className="text-[12px] mt-3" style={{ color: "var(--ink-3)" }}>
            Cenário: 2º turno entre Lula e direita unificada com alta probabilidade.
          </div>
        </div>

        <div className="col-span-12 md:col-span-5 grid grid-cols-2 gap-3">
          <Stat label="Treino" value={health.n_train_events.toString()} sub="eventos" />
          <Stat label="Backtest" value="94.16%" sub="6 ciclos" highlight />
          <Stat label="Selective τ=.15" value="96.1%" sub="92% cobertura" />
          <Stat label="Snapshot" value={snap.predicted_at.slice(5)} sub={snap.predicted_at.slice(0, 4)} />
        </div>
      </section>

      {/* RANKING TABLE */}
      <section className="fade-up" style={{ animationDelay: "300ms" }}>
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="text-[12px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Ranking completo
          </h2>
          <span className="text-[11px]" style={{ color: "var(--ink-4)" }}>
            Bolsonaro filtrado · inelegível TSE até 2030
          </span>
        </div>

        <div className="rounded-xl overflow-hidden"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          {sorted.map((c, i) => {
            const pct = (c.p_winner ?? 0) * 100;
            const color = REGIME_COLOR[c.regime || "center"];
            const isFirst = i === 0;
            return (
              <div key={c.nome} className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-white/[0.02]"
                style={{ borderTop: i > 0 ? "1px solid var(--line)" : "none" }}>
                <span className="mono text-[12px] tabular w-6"
                  style={{ color: isFirst ? "var(--gold)" : "var(--ink-4)" }}>
                  {(i + 1).toString().padStart(2, "0")}
                </span>
                <div className="w-1 h-10 rounded-sm flex-shrink-0"
                  style={{ background: color }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline gap-2">
                    <span className="text-[15px] font-semibold">{c.nome}</span>
                    <span className="text-[11px] mono" style={{ color: "var(--ink-3)" }}>
                      {c.partido}
                    </span>
                    {c.incumbente === 1 && (
                      <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded"
                        style={{ background: "rgba(251,191,36,0.1)", color: "var(--gold)",
                                 border: "1px solid rgba(251,191,36,0.3)" }}>
                        incumb
                      </span>
                    )}
                  </div>
                  {c.status_note && (
                    <div className="text-[12px] mt-0.5" style={{ color: "var(--ink-3)" }}>
                      {c.status_note}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="w-32 h-1.5 rounded-full overflow-hidden"
                    style={{ background: "var(--bg-soft)" }}>
                    <div className="h-full rounded-full"
                      style={{ width: `${pct}%`, background: color, opacity: 0.85 }} />
                  </div>
                  <span className="mono text-[18px] tabular font-medium w-16 text-right"
                    style={{ color: isFirst ? "var(--gold)" : "var(--ink)" }}>
                    {pct.toFixed(1)}<span className="text-[12px] opacity-60">%</span>
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* METHODOLOGY NOTE */}
      <section className="mt-12 grid grid-cols-12 gap-8 fade-up"
        style={{ animationDelay: "400ms", borderTop: "1px solid var(--line)", paddingTop: "32px" }}>
        <div className="col-span-12 md:col-span-4">
          <h3 className="text-[12px] mono uppercase tracking-[0.2em] mb-2"
            style={{ color: "var(--ink-3)" }}>
            Como ler
          </h3>
        </div>
        <div className="col-span-12 md:col-span-8 text-[14px] leading-relaxed space-y-2"
          style={{ color: "var(--ink-2)" }}>
          <p>
            Modelo PC-CRD cohort + Linzer ensemble (50/50). Treinado em{" "}
            {health.n_train_events} eventos políticos brasileiros (2010 – 2024).
            Validação histórica: <strong style={{ color: "var(--ink)" }}>94.16% acc</strong>{" "}
            year-fold cross-validation.
          </p>
          <p style={{ color: "var(--ink-3)" }}>
            Probabilidades são priors baseados em incumbência + regime + pesquisas
            agregadas iniciais. Snapshot {snap.horizon_days} dias antes da eleição.
            Recalibragem mensal conforme novos polls. Bolsonaro filtrado por
            inelegibilidade TSE até 2030. Demais candidaturas marcadas{" "}
            <span className="mono">speculation</span> — sem registro formal.
          </p>
        </div>
      </section>
    </Shell>
  );
}

function Stat({ label, value, sub, highlight = false }: {
  label: string; value: string; sub: string; highlight?: boolean;
}) {
  return (
    <div className="rounded-lg p-4"
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--line)",
      }}>
      <div className="text-[10px] mono uppercase tracking-[0.15em]"
        style={{ color: "var(--ink-3)" }}>{label}</div>
      <div className="serif text-[28px] leading-none tabular mt-2 font-light"
        style={{ color: highlight ? "var(--gold)" : "var(--ink)" }}>
        {value}
      </div>
      <div className="text-[11px] mt-1" style={{ color: "var(--ink-4)" }}>{sub}</div>
    </div>
  );
}
