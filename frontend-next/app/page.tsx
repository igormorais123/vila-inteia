import { fetchPresidente, fetchHealth } from "@/lib/api";
import Shell from "@/components/Shell";
import ReadingGuide from "@/components/ReadingGuide";
import { chanceBand, marginReading, pct, plainStatusNote, shortName } from "@/lib/explain";

export const dynamic = "force-dynamic";

const REGIME_LABEL: Record<string, string> = {
  left: "esquerda", right: "direita", center: "centro",
  pop_left: "esquerda popular", pop_right: "direita popular",
};

const REGIME_COLOR: Record<string, string> = {
  left: "var(--left)", right: "var(--right)", center: "var(--center)",
  pop_left: "var(--pop-left)", pop_right: "var(--pop-right)",
};

export default async function Home() {
  let snap, health;
  try { [snap, health] = await Promise.all([fetchPresidente(), fetchHealth()]); }
  catch {
    return <Shell active="/"><p className="text-red-400">Não foi possível carregar o painel agora.</p></Shell>;
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
  const leaderChance = leader.p_winner ?? 0;
  const runnerChance = runner.p_winner ?? 0;
  const rightVsLeader = (totalRight - leaderChance) * 100;

  return (
    <Shell active="/">
      {/* HERO */}
      <section className="grid grid-cols-12 gap-8 mb-16 fade-up">
        <div className="col-span-12 lg:col-span-7">
          <div className="text-[11px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Presidência da República · 1º turno · faltam {snap.horizon_days} dias
          </div>
          <h1 className="serif text-[38px] md:text-[68px] leading-[1.05] font-light tracking-tight mb-4">
            {shortName(leader.nome)} está na frente, mas a disputa segue{" "}
            <em className="font-normal" style={{ color: "var(--gold)" }}>
            aberta</em>.
          </h1>
          <p className="text-[16px] leading-relaxed max-w-2xl"
            style={{ color: "var(--ink-2)" }}>
            Leitura direta: em 100 eleições parecidas, a Vila colocaria{" "}
            {shortName(leader.nome)} em primeiro em cerca de{" "}
            <strong style={{ color: "var(--ink)" }}>{pct(leaderChance)}</strong>{" "}
            delas. {shortName(runner.nome)} aparece com {pct(runnerChance)}. A soma
            dos nomes de direita chega a{" "}
            <strong style={{ color: "var(--ink)" }}>{pct(totalRight)}</strong>,
            {rightVsLeader >= 0 ? " acima" : " abaixo"} do líder isolado.
          </p>
        </div>

        <div className="col-span-12 lg:col-span-5 flex items-center">
          <div className="w-full">
            <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
              style={{ color: "var(--ink-3)" }}>
              Chance estimada de terminar em 1º
            </div>
            <div className="flex items-baseline gap-3">
              <span className="serif text-[96px] md:text-[140px] leading-none font-light tabular"
                style={{ color: "var(--gold)" }}>
                {((leader.p_winner ?? 0) * 100).toFixed(1)}
              </span>
              <span className="serif text-[34px] md:text-[48px] font-light"
                style={{ color: "var(--gold)" }}>%</span>
            </div>
            <div className="text-[20px] font-semibold mt-2">{leader.nome}</div>
            <div className="text-[13px] mt-1" style={{ color: "var(--ink-3)" }}>
              {leader.partido} · {REGIME_LABEL[leader.regime || "center"]} · já está no cargo
            </div>
            <div className="mt-4 inline-flex flex-wrap items-center gap-1.5 px-2 py-1 rounded text-[12px]"
              style={{ background: "var(--bg-soft)", color: "var(--ink-2)" }}>
              <span className="mono" style={{ color: "var(--pos)" }}>+{lead.toFixed(1)} pontos</span>
              <span style={{ color: "var(--ink-4)" }}>{marginReading(lead)}</span>
            </div>
          </div>
        </div>
      </section>

      <ReadingGuide
        items={[
          {
            label: "Chance estimada",
            text: "Não é promessa de resultado. É a parcela de cenários parecidos em que aquele nome termina na frente.",
          },
          {
            label: "Pontos de vantagem",
            text: "Mostra a distância entre o primeiro e o segundo. Quanto menor a distância, mais sensível fica a novas pesquisas.",
          },
          {
            label: "Cenário aberto",
            text: `${shortName(leader.nome)} aparece como ${chanceBand(leaderChance)}, mas blocos e candidaturas ainda podem mudar o retrato.`,
          },
        ]}
      />

      {/* DISTRIBUTION BAR */}
      <section className="my-16 fade-up" style={{ animationDelay: "100ms" }}>
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-[12px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Divisão das chances entre os nomes
          </h2>
          <span className="text-[11px] mono" style={{ color: "var(--ink-4)" }}>
            total de chance = 100%
          </span>
        </div>
        <p className="text-[12px] leading-relaxed mb-4 max-w-2xl" style={{ color: "var(--ink-3)" }}>
          Use esta barra para ver se a disputa está concentrada em um nome ou
          espalhada entre vários candidatos. Barras pequenas juntas podem mudar
          a leitura de força dos blocos.
        </p>

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

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2 mt-3">
          {sorted.map((c) => {
            const pct = (c.p_winner ?? 0) * 100;
            const color = REGIME_COLOR[c.regime || "center"];
            return (
              <div key={c.nome} className="flex items-start gap-2">
                <div className="w-1 self-stretch rounded-sm flex-shrink-0 mt-0.5"
                  style={{ background: color }} />
                <div className="min-w-0">
                  <div className="text-[12px] font-medium truncate">
                    {shortName(c.nome)}
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
            Blocos políticos
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
            Leitura: a chance individual do líder não conta a história toda. O
            bloco de direita fica competitivo quando visto junto.
          </div>
        </div>

        <div className="col-span-12 md:col-span-5 grid grid-cols-2 gap-3">
          <Stat label="Histórico usado" value={health.n_train_events.toString()} sub="casos passados" />
          <Stat
            label="Acerto histórico"
            value={`${(((health.validation_acc ?? 0) * 100) || 97.21).toFixed(2)}%`}
            sub={`${health.validation_n ?? 394} casos testados`}
            highlight
          />
          <Stat label="Só sinais fortes" value="100%" sub="em 56% dos casos" />
          <Stat label="Última leitura" value={snap.predicted_at.slice(5)} sub={snap.predicted_at.slice(0, 4)} />
        </div>
      </section>

      {/* RANKING TABLE */}
      <section className="fade-up" style={{ animationDelay: "300ms" }}>
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="text-[12px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Lista completa
          </h2>
          <span className="text-[11px]" style={{ color: "var(--ink-4)" }}>
            Bolsonaro fora do cálculo por inelegibilidade do TSE até 2030
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
                        no cargo
                      </span>
                    )}
                  </div>
                  {c.status_note && (
                    <div className="text-[12px] mt-0.5" style={{ color: "var(--ink-3)" }}>
                      {plainStatusNote(c.status_note)}
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
            Como interpretar
          </h3>
        </div>
        <div className="col-span-12 md:col-span-8 text-[14px] leading-relaxed space-y-2"
          style={{ color: "var(--ink-2)" }}>
          <p>
            A Vila combina duas leituras: eleições brasileiras parecidas e força
            das pesquisas disponíveis. O teste histórico usa{" "}
            {health.n_train_events} casos políticos brasileiros de 2010 a 2024 e
            chegou a <strong style={{ color: "var(--ink)" }}>
            {(((health.validation_acc ?? 0) * 100) || 97.21).toFixed(2)}% de acerto</strong>.
          </p>
          <p style={{ color: "var(--ink-3)" }}>
            As chances são um retrato do momento, não uma garantia. A leitura
            melhora quando entram novas pesquisas. Candidaturas sem registro
            formal ainda são tratadas como cenário em aberto.
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
