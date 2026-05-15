"use client";
import { useState } from "react";
import { Calculator } from "lucide-react";
import Shell from "@/components/Shell";
import ReadingGuide from "@/components/ReadingGuide";
import { postPredict, type PredictResponse } from "@/lib/api";
import { chanceBand } from "@/lib/explain";

export default function Custom() {
  const [cargo, setCargo] = useState("governador");
  const [lead, setLead] = useState(8);
  const [days, setDays] = useState(45);
  const [incumb, setIncumb] = useState(0);
  const [regime, setRegime] = useState("center");
  const [apiKey, setApiKey] = useState("");
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    setErr(null); setLoading(true);
    try {
      const r = await postPredict({
        cargo, poll_lead_pp: lead, days_to_election: days,
        incumbente: incumb, regime,
      }, apiKey || undefined);
      setResult(r);
    } catch {
      setErr("Não foi possível calcular agora. Verifique os campos e tente novamente.");
    } finally { setLoading(false); }
  }

  return (
    <Shell active="/custom">
      <header className="mb-8 fade-up">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Cenário simples
        </div>
        <h1 className="serif text-[34px] md:text-[48px] leading-[1.05] font-light tracking-tight">
          Calcule a chance de vitória sem linguagem técnica.
        </h1>
        <p className="text-[15px] mt-4 max-w-2xl" style={{ color: "var(--ink-2)" }}>
          Informe cargo, vantagem nas pesquisas, tempo até a eleição e campo
          político. A resposta mostra uma chance final e de onde ela veio.
        </p>
      </header>

      <ReadingGuide
        title="Como preencher"
        items={[
          {
            label: "Cargo e campo",
            text: "Dizem que tipo de eleição será comparada com casos anteriores.",
          },
          {
            label: "Vantagem na pesquisa",
            text: "Pontos acima de zero indicam liderança; pontos abaixo indicam desvantagem.",
          },
          {
            label: "Tempo até a eleição",
            text: "Quanto mais longe da urna, maior a incerteza e mais cautelosa fica a leitura.",
          },
        ]}
      />

      <div className="grid grid-cols-12 gap-8 fade-up mt-8" style={{ animationDelay: "100ms" }}>
        <div className="col-span-12 md:col-span-7 space-y-6">
          <Section title="Cargo">
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-1.5">
              {[
                { v: "presidente", l: "Presidente" },
                { v: "governador", l: "Governador" },
                { v: "senador", l: "Senador" },
                { v: "legislativo", l: "Legislativo" },
                { v: "prefeito", l: "Prefeito" },
              ].map((o) => (
                <button key={o.v} onClick={() => setCargo(o.v)}
                  className="py-2 rounded text-[13px] font-medium transition-colors"
                  style={{
                    background: cargo === o.v ? "var(--gold)" : "var(--bg-card)",
                    color: cargo === o.v ? "#000" : "var(--ink-2)",
                    border: `1px solid ${cargo === o.v ? "var(--gold)" : "var(--line)"}`,
                  }}>
                  {o.l}
                </button>
              ))}
            </div>
          </Section>

          <Section title={`Vantagem nas pesquisas: ${lead > 0 ? "+" : ""}${lead} pontos`}
            sub="negativo quer dizer que está atrás">
            <input type="range" min={-30} max={30} step={0.5} value={lead}
              onChange={(e) => setLead(parseFloat(e.target.value))}
              className="w-full" style={{ accentColor: "var(--gold)" }} />
            <div className="flex justify-between text-[10px] mono mt-1"
              style={{ color: "var(--ink-4)" }}>
              <span>-30</span><span>0</span><span>+30</span>
            </div>
          </Section>

          <Section title={`Dias até a eleição: ${days}`}
            sub={days <= 30 ? "campanha avançada" : days <= 90 ? "fase intermediária" : "longo prazo"}>
            <input type="range" min={0} max={365} step={1} value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-full" style={{ accentColor: "var(--gold)" }} />
          </Section>

          <div className="grid grid-cols-2 gap-3">
            <Section title="Já está no cargo?">
              <div className="grid grid-cols-2 gap-1.5">
                {[{ v: 0, l: "Não" }, { v: 1, l: "Sim" }].map((o) => (
                  <button key={o.v} onClick={() => setIncumb(o.v)}
                    className="py-2 rounded text-[13px] font-medium transition-colors"
                    style={{
                      background: incumb === o.v ? "var(--bg-soft)" : "var(--bg-card)",
                      color: incumb === o.v ? "var(--ink)" : "var(--ink-3)",
                      border: `1px solid ${incumb === o.v ? "var(--line-strong)" : "var(--line)"}`,
                    }}>
                    {o.l}
                  </button>
                ))}
              </div>
            </Section>
            <Section title="Campo político">
              <select value={regime} onChange={(e) => setRegime(e.target.value)}
                className="w-full py-2 px-3 rounded text-[13px] mono"
                style={{ background: "var(--bg-card)", color: "var(--ink)",
                         border: "1px solid var(--line)" }}>
                <option value="left">Esquerda</option>
                <option value="center">Centro</option>
                <option value="right">Direita</option>
                <option value="pop_left">Esquerda popular</option>
                <option value="pop_right">Direita popular</option>
              </select>
            </Section>
          </div>

          <Section title="Chave do cliente (opcional)" sub="contas profissionais">
            <input type="text" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
              placeholder="vila_pol_..."
              className="w-full py-2 px-3 rounded text-[13px] mono"
              style={{ background: "var(--bg-card)", color: "var(--ink)",
                       border: "1px solid var(--line)" }} />
          </Section>

          <button onClick={submit} disabled={loading}
            className="w-full py-3 rounded-lg font-semibold text-[14px] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            style={{
              background: "linear-gradient(180deg, var(--gold), #d97706)",
              color: "#000",
              boxShadow: "0 4px 24px rgba(251,191,36,0.2)",
            }}>
            <Calculator size={16} />
            {loading ? "Calculando…" : "Calcular chance"}
          </button>
        </div>

        <div className="col-span-12 md:col-span-5">
          <div className="sticky top-20 rounded-xl p-8"
            style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
            {!result && !err && (
              <div className="text-center py-12">
                <div className="serif text-[140px] leading-none font-light tabular"
                  style={{ color: "var(--bg-soft)" }}>?</div>
                <p className="text-[13px] mt-4" style={{ color: "var(--ink-4)" }}>
                  Resultado aparecerá aqui
                </p>
              </div>
            )}
            {err && (
              <div className="rounded p-3 text-[13px] mono"
                style={{ background: "rgba(239,68,68,0.1)", color: "var(--neg)",
                         border: "1px solid rgba(239,68,68,0.3)" }}>
                {err}
              </div>
            )}
            {result && (
              <div>
                <div className="text-[10px] mono uppercase tracking-[0.2em] mb-3"
                  style={{ color: "var(--ink-3)" }}>
                  Chance final
                </div>
                <div className="serif text-[100px] leading-none font-light tabular"
                  style={{ color: "var(--gold)" }}>
                  {(result.p_blend * 100).toFixed(1)}
                  <span className="text-[40px] opacity-60">%</span>
                </div>
                <div className="text-[13px] mt-3" style={{ color: "var(--ink-2)" }}>
                  {chanceBand(result.p_blend)}
                </div>

                <div className="mt-8 pt-6 grid grid-cols-2 gap-4"
                  style={{ borderTop: "1px solid var(--line)" }}>
                  <Comp label="Histórico parecido" v={result.p_cohort} />
                  <Comp label="Força da pesquisa" v={result.p_linzer} />
                </div>

                <div className="mt-6 grid grid-cols-3 gap-3 text-[11px] mono">
                  <KV k="cargo" v={cargo} />
                  <KV k="casos parecidos" v={result.cohort_n.toString()} />
                  <KV k="dias até eleição" v={`${result.horizon_days}`} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Shell>
  );
}

function Section({ title, sub, children }: { title: string; sub?: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
        <span className="text-[11px] mono uppercase tracking-[0.15em]"
          style={{ color: "var(--ink-3)" }}>{title}</span>
        {sub && <span className="text-[10px]" style={{ color: "var(--ink-4)" }}>{sub}</span>}
      </div>
      {children}
    </div>
  );
}

function Comp({ label, v }: { label: string; v: number }) {
  return (
    <div>
      <div className="text-[10px] mono uppercase tracking-[0.15em]"
        style={{ color: "var(--ink-4)" }}>{label}</div>
      <div className="serif text-[32px] leading-none tabular font-light mt-1"
        style={{ color: "var(--ink)" }}>
        {(v * 100).toFixed(1)}<span className="text-[14px] opacity-50">%</span>
      </div>
    </div>
  );
}

function KV({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <div style={{ color: "var(--ink-4)" }}>{k}</div>
      <div className="mt-0.5" style={{ color: "var(--ink-2)" }}>{v}</div>
    </div>
  );
}
