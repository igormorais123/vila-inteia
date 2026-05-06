"use client";
import { useState } from "react";
import Shell from "@/components/Shell";
import { postPredict, type PredictResponse } from "@/lib/api";

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
    } catch (e) {
      setErr((e as Error).message);
    } finally { setLoading(false); }
  }

  return (
    <Shell active="/custom">
      <header className="mb-10 fade-up">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Cenário customizado
        </div>
        <h1 className="serif text-[48px] leading-[1.05] font-light tracking-tight">
          Calcule P(vitória) para qualquer combinação.
        </h1>
      </header>

      <div className="grid grid-cols-12 gap-8 fade-up" style={{ animationDelay: "100ms" }}>
        <div className="col-span-12 md:col-span-7 space-y-6">
          <Section title="Cargo">
            <div className="grid grid-cols-5 gap-1.5">
              {[
                { v: "presidente", l: "Pres" },
                { v: "governador", l: "Gov" },
                { v: "senador", l: "Senador" },
                { v: "legislativo", l: "Legisl" },
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

          <Section title={`Vantagem nas pesquisas: ${lead > 0 ? "+" : ""}${lead}pp`}
            sub="negativo = atrás do líder">
            <input type="range" min={-30} max={30} step={0.5} value={lead}
              onChange={(e) => setLead(parseFloat(e.target.value))}
              className="w-full" style={{ accentColor: "var(--gold)" }} />
            <div className="flex justify-between text-[10px] mono mt-1"
              style={{ color: "var(--ink-4)" }}>
              <span>-30</span><span>0</span><span>+30</span>
            </div>
          </Section>

          <Section title={`Dias até eleição: ${days}`}
            sub={days <= 30 ? "campanha avançada" : days <= 90 ? "fase intermediária" : "longo prazo"}>
            <input type="range" min={0} max={365} step={1} value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-full" style={{ accentColor: "var(--gold)" }} />
          </Section>

          <div className="grid grid-cols-2 gap-3">
            <Section title="Incumbente">
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
            <Section title="Regime">
              <select value={regime} onChange={(e) => setRegime(e.target.value)}
                className="w-full py-2 px-3 rounded text-[13px] mono"
                style={{ background: "var(--bg-card)", color: "var(--ink)",
                         border: "1px solid var(--line)" }}>
                <option value="left">Esquerda</option>
                <option value="center">Centro</option>
                <option value="right">Direita</option>
                <option value="pop_left">Pop. esquerda</option>
                <option value="pop_right">Pop. direita</option>
              </select>
            </Section>
          </div>

          <Section title="X-API-Key (opcional)" sub="cliente pro/enterprise">
            <input type="text" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
              placeholder="vila_pol_..."
              className="w-full py-2 px-3 rounded text-[13px] mono"
              style={{ background: "var(--bg-card)", color: "var(--ink)",
                       border: "1px solid var(--line)" }} />
          </Section>

          <button onClick={submit} disabled={loading}
            className="w-full py-3 rounded-lg font-semibold text-[14px] transition-all disabled:opacity-50"
            style={{
              background: "linear-gradient(180deg, var(--gold), #d97706)",
              color: "#000",
              boxShadow: "0 4px 24px rgba(251,191,36,0.2)",
            }}>
            {loading ? "Calculando…" : "Calcular probabilidade"}
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
                  Configure parâmetros e clique calcular
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
                  Probabilidade ensemble
                </div>
                <div className="serif text-[100px] leading-none font-light tabular"
                  style={{ color: "var(--gold)" }}>
                  {(result.p_blend * 100).toFixed(1)}
                  <span className="text-[40px] opacity-60">%</span>
                </div>
                <div className="text-[13px] mt-3" style={{ color: "var(--ink-2)" }}>
                  {result.p_blend > 0.7 ? "Forte favorito"
                    : result.p_blend > 0.55 ? "Favorito leve"
                    : result.p_blend > 0.45 ? "Tossup"
                    : result.p_blend > 0.3 ? "Underdog"
                    : "Underdog forte"}
                </div>

                <div className="mt-8 pt-6 grid grid-cols-2 gap-4"
                  style={{ borderTop: "1px solid var(--line)" }}>
                  <Comp label="Cohort" v={result.p_cohort} />
                  <Comp label="Linzer" v={result.p_linzer} />
                </div>

                <div className="mt-6 grid grid-cols-3 gap-3 text-[11px] mono">
                  <KV k="tier" v={result.cohort_tier} />
                  <KV k="n cohort" v={result.cohort_n.toString()} />
                  <KV k="horizon" v={`${result.horizon_days}d`} />
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
      <div className="flex items-baseline justify-between mb-2">
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
