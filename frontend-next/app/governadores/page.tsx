import { fetchGovernadorAll } from "@/lib/api";
import Shell from "@/components/Shell";

export const dynamic = "force-dynamic";

const UF_NOMES: Record<string, string> = {
  SP: "São Paulo", RJ: "Rio de Janeiro", MG: "Minas Gerais", RS: "Rio Grande do Sul",
  BA: "Bahia", CE: "Ceará", PE: "Pernambuco", PR: "Paraná",
  GO: "Goiás", SC: "Santa Catarina",
};

const REGIME_COLOR: Record<string, string> = {
  left: "var(--left)", right: "var(--right)", center: "var(--center)",
  pop_left: "var(--pop-left)", pop_right: "var(--pop-right)",
};

export default async function Governadores() {
  let data;
  try { data = await fetchGovernadorAll(); }
  catch (e) {
    return <Shell active="/governadores"><p className="text-red-400">{(e as Error).message}</p></Shell>;
  }

  const ufs = Object.keys(data.by_uf).sort();
  const competitive = ufs.filter((uf) => {
    const top = Math.max(...data.by_uf[uf].map((c: any) => c.p_winner ?? 0));
    return top < 0.95 && data.by_uf[uf].length >= 2;
  });
  const consolidated = ufs.filter((uf) => !competitive.includes(uf));

  return (
    <Shell active="/governadores">
      <header className="mb-12 fade-up">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Estaduais 2026 · {ufs.length} estados
        </div>
        <h1 className="serif text-[56px] leading-[1.05] font-light tracking-tight">
          Incumbentes em vantagem em <em className="font-normal" style={{ color: "var(--gold)" }}>
          {ufs.length - competitive.length} dos {ufs.length}</em> estados mapeados.
        </h1>
        <p className="text-[15px] mt-4 max-w-2xl" style={{ color: "var(--ink-2)" }}>
          {competitive.length} corrida{competitive.length === 1 ? "" : "s"} competitiva{competitive.length === 1 ? "" : "s"} com oposição mapeada.
          Estados sem oposição definida no registry mostram incumbente em 100%
          — reflete ausência de candidato cadastrado, não certeza factual.
        </p>
      </header>

      {competitive.length > 0 && (
        <section className="mb-16 fade-up" style={{ animationDelay: "100ms" }}>
          <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Corridas competitivas
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {competitive.map((uf) => (
              <CompetitiveUF key={uf} uf={uf} cands={data.by_uf[uf]} />
            ))}
          </div>
        </section>
      )}

      {consolidated.length > 0 && (
        <section className="fade-up" style={{ animationDelay: "200ms" }}>
          <h2 className="text-[12px] mono uppercase tracking-[0.2em] mb-4"
            style={{ color: "var(--ink-3)" }}>
            Reeleições esperadas
          </h2>
          <div className="rounded-xl overflow-hidden"
            style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
            {consolidated.map((uf, i) => {
              const top = data.by_uf[uf].sort((a: any, b: any) => (b.p_winner ?? 0) - (a.p_winner ?? 0))[0];
              const color = REGIME_COLOR[top.regime || "center"];
              return (
                <div key={uf} className="flex items-center gap-4 px-5 py-3.5 transition-colors hover:bg-white/[0.02]"
                  style={{ borderTop: i > 0 ? "1px solid var(--line)" : "none" }}>
                  <div className="mono text-[13px] font-bold w-10"
                    style={{ color: "var(--gold)" }}>
                    {uf}
                  </div>
                  <div className="text-[12px] flex-shrink-0 w-32"
                    style={{ color: "var(--ink-3)" }}>
                    {UF_NOMES[uf] || uf}
                  </div>
                  <div className="w-1 h-8 rounded-sm flex-shrink-0"
                    style={{ background: color }} />
                  <div className="flex-1 text-[14px] font-medium">{top.nome}</div>
                  <div className="text-[12px] mono" style={{ color: "var(--ink-3)" }}>
                    {top.partido}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </Shell>
  );
}

function CompetitiveUF({ uf, cands }: { uf: string; cands: any[] }) {
  const sorted = [...cands].sort((a, b) => (b.p_winner ?? 0) - (a.p_winner ?? 0));
  const [top, ...rest] = sorted;
  const topColor = REGIME_COLOR[top.regime || "center"];

  return (
    <div className="rounded-xl p-5"
      style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
      <div className="flex items-baseline gap-3 mb-4">
        <span className="serif text-[36px] leading-none font-light tabular"
          style={{ color: "var(--gold)" }}>{uf}</span>
        <span className="text-[13px]" style={{ color: "var(--ink-3)" }}>
          {UF_NOMES[uf]}
        </span>
        <span className="ml-auto text-[10px] mono uppercase tracking-wider"
          style={{ color: "var(--ink-4)" }}>
          {sorted.length} candidatos
        </span>
      </div>

      <div className="flex h-10 rounded overflow-hidden mb-3"
        style={{ border: "1px solid var(--line)" }}>
        {sorted.map((c, i) => {
          const pct = (c.p_winner ?? 0) * 100;
          const color = REGIME_COLOR[c.regime || "center"];
          return (
            <div key={c.nome}
              className="flex items-center justify-center"
              style={{
                width: `${pct}%`,
                background: color,
                opacity: i === 0 ? 1 : 0.65,
                borderRight: i < sorted.length - 1 ? "1px solid var(--bg)" : "none",
              }}>
              <span className="text-[10px] mono font-semibold text-black/85">
                {pct >= 20 ? `${pct.toFixed(0)}%` : ""}
              </span>
            </div>
          );
        })}
      </div>

      <div className="space-y-2">
        {sorted.map((c, i) => {
          const pct = (c.p_winner ?? 0) * 100;
          const color = REGIME_COLOR[c.regime || "center"];
          return (
            <div key={c.nome} className="flex items-center gap-3">
              <div className="w-1 self-stretch min-h-[1.2rem] rounded-sm flex-shrink-0"
                style={{ background: color }} />
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-medium truncate">{c.nome}</div>
                <div className="text-[10px] mono" style={{ color: "var(--ink-4)" }}>
                  {c.partido} · {c.incumbente ? "incumbente" : "desafiante"}
                </div>
              </div>
              <span className="mono text-[15px] tabular font-semibold w-14 text-right"
                style={{ color: i === 0 ? "var(--gold)" : "var(--ink)" }}>
                {pct.toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
