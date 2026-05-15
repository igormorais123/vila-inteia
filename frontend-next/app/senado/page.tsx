import { fetchSenador } from "@/lib/api";
import Shell from "@/components/Shell";
import ReadingGuide from "@/components/ReadingGuide";
import { plainStatusNote } from "@/lib/explain";

export const dynamic = "force-dynamic";

const UF_NOMES: Record<string, string> = {
  SP: "São Paulo", RJ: "Rio de Janeiro", MG: "Minas Gerais", RS: "Rio Grande do Sul",
};

export default async function Senado() {
  let data;
  try { data = await fetchSenador(); }
  catch {
    return <Shell active="/senado"><p className="text-red-400">Não foi possível carregar a tela do Senado agora.</p></Shell>;
  }

  return (
    <Shell active="/senado">
      <header className="mb-8 fade-up max-w-3xl">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Senado 2026 · 1/3 das cadeiras em disputa
        </div>
        <h1 className="serif text-[40px] md:text-[56px] leading-[1.05] font-light tracking-tight">
          Cadeiras de <em className="font-normal" style={{ color: "var(--gold)" }}>2018</em>{" "}
          chegam ao fim, ainda sem pesquisas reais.
        </h1>
        <p className="text-[15px] mt-4" style={{ color: "var(--ink-2)" }}>
          Os 81 senadores cumprem mandatos de 8 anos, alternando renovações de
          1/3 e 2/3. Em 2026, vencem as cadeiras eleitas em 2018. A lista abaixo
          mostra os <strong style={{ color: "var(--ink)" }}>titulares cuja cadeira vence</strong>,
          não candidatos confirmados. Como ainda não há pesquisas reais, as chances
          exibidas são só uma base inicial para quem ocupa a cadeira, não uma
          previsão de vencedor.
        </p>
      </header>

      <div className="mb-10 fade-up" style={{ animationDelay: "75ms" }}>
        <ReadingGuide
          title="Como interpretar"
          items={[
            {
              label: "O que a tela mostra",
              text: "As cadeiras cujo mandato termina em janeiro de 2027.",
            },
            {
              label: "O que ainda não mostra",
              text: "Não é lista final de candidatos, porque as candidaturas ainda podem mudar.",
            },
            {
              label: "Como usar",
              text: "Use como mapa inicial; a previsão melhora quando surgirem pesquisas reais.",
            },
          ]}
        />
      </div>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-3 fade-up"
        style={{ animationDelay: "100ms" }}>
        {data.candidates.map((c) => {
          const p = ((c.p_raw ?? c.p_winner ?? 0) as number) * 100;
          return (
            <div key={c.nome} className="rounded-xl p-6 transition-all hover:-translate-y-0.5"
              style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
              <div className="flex items-baseline gap-3 mb-3">
                <span className="serif text-[40px] leading-none font-light tabular"
                  style={{ color: "var(--gold)" }}>{c.uf}</span>
                <span className="text-[13px]" style={{ color: "var(--ink-3)" }}>
                  {UF_NOMES[c.uf || ""] || c.uf}
                </span>
              </div>
              <div className="text-[18px] font-semibold leading-tight">
                {c.nome}
              </div>
              <div className="text-[12px] mono mt-1" style={{ color: "var(--ink-3)" }}>
                {c.partido} · mandato 2019 – jan/2027
              </div>
              {c.status_note && (
                <p className="text-[12px] mt-3 italic" style={{ color: "var(--ink-3)" }}>
                  {plainStatusNote(c.status_note)}
                </p>
              )}
              <div className="mt-5 pt-4" style={{ borderTop: "1px solid var(--line)" }}>
                <div className="flex items-baseline justify-between mb-2">
                  <span className="text-[10px] mono uppercase tracking-[0.15em]"
                    style={{ color: "var(--ink-4)" }}>
                    Base inicial do titular
                  </span>
                  <span className="mono text-[15px] tabular"
                    style={{ color: "var(--ink-2)" }}>
                    {p.toFixed(1)}%
                  </span>
                </div>
                <div className="h-1 rounded-full overflow-hidden"
                  style={{ background: "var(--bg-soft)" }}>
                  <div className="h-full rounded-full"
                    style={{ width: `${p}%`, background: "var(--ink-4)" }} />
                </div>
              </div>
            </div>
          );
        })}
      </section>

      <p className="mt-12 text-[13px] max-w-2xl" style={{ color: "var(--ink-3)" }}>
        A cobertura completa do Senado melhora quando pesquisas reais de
        candidatos às vagas começarem a aparecer, esperado a partir de agosto de
        2026, próximo ao registro oficial das candidaturas.
      </p>
    </Shell>
  );
}
