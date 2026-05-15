"use client";
import { useEffect, useMemo, useState } from "react";
import { Plus, Share2, Trash2 } from "lucide-react";
import Shell from "@/components/Shell";
import ReadingGuide from "@/components/ReadingGuide";
import Trajectory from "@/components/Trajectory";
import SecondRound from "@/components/SecondRound";
import { predictBlend, normalize, type SimCandidate } from "@/lib/predict";
import { chanceBand } from "@/lib/explain";

const REGIME_COLOR: Record<string, string> = {
  left: "var(--left)", right: "var(--right)", center: "var(--center)",
  pop_left: "var(--pop-left)", pop_right: "var(--pop-right)",
};

const REGIME_LABEL: Record<string, string> = {
  left: "esquerda", right: "direita", center: "centro",
  pop_left: "esquerda popular", pop_right: "direita popular",
};

const PRESETS = {
  presidencia_2026: [
    { id: "1", nome: "Lula", partido: "PT", regime: "left", incumbente: 1, leadPp: 0 },
    { id: "2", nome: "Tarcísio", partido: "REP", regime: "right", incumbente: 0, leadPp: -8 },
    { id: "3", nome: "Ratinho Jr", partido: "PSD", regime: "right", incumbente: 0, leadPp: -22 },
    { id: "4", nome: "Zema", partido: "NOVO", regime: "right", incumbente: 0, leadPp: -25 },
    { id: "5", nome: "Boulos", partido: "PSOL", regime: "pop_left", incumbente: 0, leadPp: -33 },
  ],
  sp_governador_2026: [
    { id: "1", nome: "Tarcísio", partido: "REP", regime: "right", incumbente: 1, leadPp: 14 },
    { id: "2", nome: "Haddad", partido: "PT", regime: "left", incumbente: 0, leadPp: -14 },
  ],
  vazio: [
    { id: "1", nome: "Candidato A", partido: "—", regime: "center", incumbente: 0, leadPp: 0 },
  ],
};

function encodeState(cands: SimCandidate[], days: number): string {
  const compact = cands.map((c) =>
    [c.nome, c.partido, c.regime, c.incumbente, c.leadPp].join("|"));
  return btoa(JSON.stringify({ c: compact, d: days }));
}

function decodeState(s: string): { candidates: SimCandidate[]; days: number } | null {
  try {
    const parsed = JSON.parse(atob(s));
    if (!parsed.c || !Array.isArray(parsed.c)) return null;
    const candidates = parsed.c.map((row: string, i: number) => {
      const [nome, partido, regime, incumb, lead] = row.split("|");
      return {
        id: String(i + 1),
        nome, partido, regime,
        incumbente: parseInt(incumb),
        leadPp: parseFloat(lead),
      };
    });
    return { candidates, days: parsed.d ?? 152 };
  } catch { return null; }
}

export default function Simular() {
  const [candidates, setCandidates] = useState<SimCandidate[]>(PRESETS.presidencia_2026);
  const [days, setDays] = useState(152);
  const [shareMsg, setShareMsg] = useState<string | null>(null);

  // Lê o cenário compartilhado quando a tela abre.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const s = params.get("s");
    if (s) {
      const decoded = decodeState(s);
      if (decoded) {
        setCandidates(decoded.candidates);
        setDays(decoded.days);
      }
    }
  }, []);

  function copyShare() {
    const s = encodeState(candidates, days);
    const url = `${window.location.origin}/simular?s=${s}`;
    navigator.clipboard.writeText(url);
    setShareMsg("link copiado");
    setTimeout(() => setShareMsg(null), 2000);
  }

  const predictions = useMemo(() => {
    const raw = candidates.map((c) => predictBlend(c, days));
    const blends = raw.map((r) => r.pBlend);
    const winners = normalize(blends);
    return candidates.map((c, i) => ({
      ...c,
      pCohort: raw[i].pCohort,
      pLinzer: raw[i].pLinzer,
      pBlend: raw[i].pBlend,
      pWinner: winners[i],
    }));
  }, [candidates, days]);

  const sorted = [...predictions].sort((a, b) => b.pWinner - a.pWinner);
  const leader = sorted[0];

  const totalLeft = sorted.filter((c) => c.regime.includes("left")).reduce((s, c) => s + c.pWinner, 0);
  const totalRight = sorted.filter((c) => c.regime.includes("right")).reduce((s, c) => s + c.pWinner, 0);
  const totalCenter = sorted.filter((c) => c.regime === "center").reduce((s, c) => s + c.pWinner, 0);

  function update(id: string, patch: Partial<SimCandidate>) {
    setCandidates((cs) => cs.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  }
  function add() {
    const id = String(Date.now());
    setCandidates((cs) => [...cs, {
      id, nome: `Candidato ${cs.length + 1}`, partido: "—",
      regime: "center", incumbente: 0, leadPp: 0,
    }]);
  }
  function remove(id: string) {
    setCandidates((cs) => cs.filter((c) => c.id !== id));
  }
  function loadPreset(key: keyof typeof PRESETS) {
    setCandidates(PRESETS[key].map((c) => ({ ...c, id: String(Math.random()) })));
  }

  return (
    <Shell active="/simular">
      <header className="mb-8 max-w-3xl">
        <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
          style={{ color: "var(--ink-3)" }}>
          Simulador · cenários possíveis
        </div>
        <h1 className="serif text-[40px] md:text-[52px] leading-[1.05] font-light tracking-tight">
          Monte uma disputa e veja quem ganha força.
        </h1>
        <p className="text-[15px] mt-4" style={{ color: "var(--ink-2)" }}>
          A leitura usa linguagem de operação: vantagem nas pesquisas, dias até
          a eleição, campo político e chance de terminar em primeiro.
        </p>
      </header>

      <ReadingGuide
        title="Como usar"
        items={[
          {
            label: "O que esta tela faz",
            text: "Ela transforma uma disputa hipotética em chances de terminar em primeiro.",
          },
          {
            label: "O que você altera",
            text: "Mude candidatos, campo político, vantagem nas pesquisas e dias até a eleição.",
          },
          {
            label: "Como interpretar",
            text: "Se a chance muda muito com pequenos ajustes, o cenário ainda está instável.",
          },
        ]}
      />

      <div className="flex items-center gap-2 my-8 flex-wrap">
        <span className="text-[11px] mono uppercase tracking-wider mr-2"
          style={{ color: "var(--ink-3)" }}>Começar por:</span>
        <PresetBtn onClick={() => loadPreset("presidencia_2026")}>Presidência 2026</PresetBtn>
        <PresetBtn onClick={() => loadPreset("sp_governador_2026")}>Governo SP 2026</PresetBtn>
        <PresetBtn onClick={() => loadPreset("vazio")}>Vazio</PresetBtn>
        <div className="w-full sm:w-auto sm:ml-auto flex items-center justify-start sm:justify-end gap-2">
          {shareMsg && (
            <span className="text-[11px] mono" style={{ color: "var(--gold)" }}>
              ✓ {shareMsg}
            </span>
          )}
          <button onClick={copyShare}
            className="px-3 py-1.5 rounded text-[12px] font-medium transition-colors flex items-center gap-1.5"
            style={{
              background: "var(--bg-card)", color: "var(--ink-2)",
              border: "1px solid var(--line-strong)",
            }}>
            <Share2 size={14} />
            compartilhar
          </button>
        </div>
      </div>

      {/* HERO LIVE */}
      <section className="grid grid-cols-12 gap-8 mb-10">
        <div className="col-span-12 md:col-span-7 rounded-xl p-6"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <div className="flex items-baseline justify-between mb-4">
            <div>
              <span className="text-[11px] mono uppercase tracking-[0.2em]"
                style={{ color: "var(--ink-3)" }}>
                Divisão das chances simuladas
              </span>
              <p className="text-[12px] mt-2 max-w-md" style={{ color: "var(--ink-3)" }}>
                A barra mostra quanto cada candidatura ocupa do cenário total.
              </p>
            </div>
            <span className="text-[11px] mono" style={{ color: "var(--ink-4)" }}>
              {candidates.length} candidatos · {days} dias
            </span>
          </div>

          <div className="flex h-14 rounded overflow-hidden mb-3"
            style={{ border: "1px solid var(--line)" }}>
            {sorted.map((c, i) => {
              const pct = c.pWinner * 100;
              const color = REGIME_COLOR[c.regime || "center"];
              return (
                <div key={c.id} className="relative flex items-center justify-center transition-all"
                  style={{
                    width: `${pct}%`,
                    background: color,
                    opacity: i === 0 ? 1 : 0.7,
                    borderRight: i < sorted.length - 1 ? "1px solid var(--bg)" : "none",
                  }}>
                  <span className="text-[11px] font-semibold mono tabular text-black/85">
                    {pct >= 8 ? `${pct.toFixed(1)}%` : ""}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="grid grid-cols-3 gap-3 mt-5 pt-4"
            style={{ borderTop: "1px solid var(--line)" }}>
            <Block label="Esquerda" v={totalLeft} color="var(--left)" />
            <Block label="Centro" v={totalCenter} color="var(--center)" />
            <Block label="Direita" v={totalRight} color="var(--right)" />
          </div>
        </div>

        <div className="col-span-12 md:col-span-5 rounded-xl p-6 flex flex-col justify-between"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <div className="text-[11px] mono uppercase tracking-[0.2em] mb-3"
            style={{ color: "var(--ink-3)" }}>
            Líder do cenário
          </div>
          <div>
            <div className="serif text-[72px] md:text-[88px] leading-none font-light tabular"
              style={{ color: "var(--gold)" }}>
              {(leader.pWinner * 100).toFixed(1)}<span className="text-[36px] opacity-60">%</span>
            </div>
            <div className="text-[18px] font-semibold mt-3">{leader.nome}</div>
            <div className="text-[12px] mt-1 mono" style={{ color: "var(--ink-3)" }}>
              {leader.partido} · {REGIME_LABEL[leader.regime]} ·{" "}
              {leader.incumbente ? "já está no cargo" : "oposição"}
            </div>
            <div className="text-[12px] mt-3" style={{ color: "var(--ink-3)" }}>
              Leitura: {chanceBand(leader.pWinner)} neste desenho.
            </div>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 pt-4"
            style={{ borderTop: "1px solid var(--line)" }}>
            <Mini label="Histórico parecido" v={leader.pCohort} />
            <Mini label="Força da pesquisa" v={leader.pLinzer} />
          </div>
        </div>
      </section>

      {/* TIME SLIDER */}
      <section className="mb-10 rounded-xl p-6"
        style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
        <div className="flex items-baseline justify-between mb-3">
          <span className="text-[11px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Dias até a eleição: <span className="text-[14px] tabular ml-2"
              style={{ color: "var(--gold)" }}>{days}</span>
          </span>
          <span className="text-[11px]" style={{ color: "var(--ink-4)" }}>
            quanto mais perto da urna, menor a incerteza
          </span>
        </div>
        <input type="range" min={0} max={365} value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          className="w-full" style={{ accentColor: "var(--gold)" }} />
        <div className="flex justify-between text-[10px] mono mt-2"
          style={{ color: "var(--ink-4)" }}>
          <span>0 (eleição)</span><span>180</span><span>365</span>
        </div>
      </section>

      {/* TRAJECTORY */}
      <section className="mb-10">
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-[12px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Como a chance muda até a eleição
          </h2>
          <span className="text-[11px]" style={{ color: "var(--ink-4)" }}>
            a confiança aumenta quando a data se aproxima
          </span>
        </div>
        <div className="rounded-xl p-6"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <Trajectory candidates={candidates} currentDays={days} />
        </div>
      </section>

      {/* SECOND ROUND */}
      {predictions.length >= 2 && leader.pWinner < 0.5 && (
        <section className="mb-10">
          <SecondRound candidates={predictions} winners={predictions.map((p) => p.pWinner)} />
        </section>
      )}

      {/* CANDIDATES TABLE */}
      <section className="mb-10">
        <div className="flex items-baseline justify-between mb-4">
          <h2 className="text-[12px] mono uppercase tracking-[0.2em]"
            style={{ color: "var(--ink-3)" }}>
            Candidatos · {candidates.length}
          </h2>
          <button onClick={add}
            className="px-3 py-1.5 rounded text-[12px] font-medium transition flex items-center gap-1.5"
            style={{ background: "var(--gold)", color: "#000" }}>
            <Plus size={14} />
            adicionar
          </button>
        </div>

        <div className="rounded-xl overflow-x-auto"
          style={{ background: "var(--bg-card)", border: "1px solid var(--line)" }}>
          <div className="min-w-[760px]">
          <div className="grid grid-cols-12 gap-3 px-5 py-3 text-[10px] mono uppercase tracking-[0.15em]"
            style={{ borderBottom: "1px solid var(--line)", color: "var(--ink-4)" }}>
            <div className="col-span-3">Nome</div>
            <div className="col-span-1">Partido</div>
            <div className="col-span-2">Campo</div>
            <div className="col-span-1 text-center">No cargo</div>
            <div className="col-span-3">Vantagem na pesquisa</div>
            <div className="col-span-1 text-right">Chance</div>
            <div className="col-span-1 text-right"></div>
          </div>
          {predictions.map((c) => {
            const color = REGIME_COLOR[c.regime || "center"];
            return (
              <div key={c.id} className="grid grid-cols-12 gap-3 px-5 py-3 items-center"
                style={{ borderBottom: "1px solid var(--line)" }}>
                <div className="col-span-3 flex items-center gap-2">
                  <div className="w-1 h-7 rounded-sm flex-shrink-0"
                    style={{ background: color }} />
                  <input type="text" value={c.nome}
                    onChange={(e) => update(c.id, { nome: e.target.value })}
                    className="flex-1 bg-transparent text-[14px] font-medium px-2 py-1 rounded transition-colors"
                    style={{ border: "1px solid transparent" }}
                    onFocus={(e) => e.currentTarget.style.borderColor = "var(--line-strong)"}
                    onBlur={(e) => e.currentTarget.style.borderColor = "transparent"}
                  />
                </div>
                <div className="col-span-1">
                  <input type="text" value={c.partido}
                    onChange={(e) => update(c.id, { partido: e.target.value })}
                    className="w-full bg-transparent text-[12px] mono px-2 py-1 rounded"
                    style={{ border: "1px solid var(--line)", color: "var(--ink-2)" }}
                  />
                </div>
                <div className="col-span-2">
                  <select value={c.regime}
                    onChange={(e) => update(c.id, { regime: e.target.value })}
                    className="w-full bg-transparent text-[12px] mono px-2 py-1 rounded"
                    style={{ border: "1px solid var(--line)", color: "var(--ink-2)" }}>
                    <option value="left">esquerda</option>
                    <option value="center">centro</option>
                    <option value="right">direita</option>
                    <option value="pop_left">esquerda popular</option>
                    <option value="pop_right">direita popular</option>
                  </select>
                </div>
                <div className="col-span-1 flex justify-center">
                  <button
                    onClick={() => update(c.id, { incumbente: c.incumbente ? 0 : 1 })}
                    className="w-9 h-6 rounded-full transition-colors flex items-center px-0.5"
                    style={{
                      background: c.incumbente ? "var(--gold)" : "var(--bg-soft)",
                    }}>
                    <div className="w-5 h-5 rounded-full transition-transform"
                      style={{
                        background: c.incumbente ? "#000" : "var(--ink-3)",
                        transform: c.incumbente ? "translateX(12px)" : "translateX(0)",
                      }} />
                  </button>
                </div>
                <div className="col-span-3 flex items-center gap-2">
                  <input type="range" min={-30} max={30} step={0.5} value={c.leadPp}
                    onChange={(e) => update(c.id, { leadPp: parseFloat(e.target.value) })}
                    className="flex-1" style={{ accentColor: color }} />
                  <span className="mono text-[12px] tabular w-12 text-right"
                    style={{ color: "var(--ink-2)" }}>
                    {c.leadPp > 0 ? "+" : ""}{c.leadPp}
                  </span>
                </div>
                <div className="col-span-1 text-right">
                  <span className="mono text-[15px] tabular font-semibold"
                    style={{ color: "var(--gold)" }}>
                    {(c.pWinner * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="col-span-1 text-right">
                  <button onClick={() => remove(c.id)}
                    className="w-7 h-7 rounded transition-colors inline-flex items-center justify-center"
                    style={{ color: "var(--ink-4)", border: "1px solid var(--line)" }}
                    title="remover">
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
          </div>
        </div>
      </section>

      <p className="text-[12px]" style={{ color: "var(--ink-3)" }}>
        Este simulador é uma leitura rápida no navegador. Ele combina histórico
        de eleições parecidas com a força da pesquisa informada. Para previsões
        oficiais, use o{" "}
        <a href="/" className="underline" style={{ color: "var(--gold)" }}>painel principal</a>.
      </p>
    </Shell>
  );
}

function PresetBtn({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className="px-3 py-1.5 rounded text-[12px] font-medium transition-colors"
      style={{
        background: "var(--bg-card)", color: "var(--ink-2)",
        border: "1px solid var(--line)",
      }}>
      {children}
    </button>
  );
}

function Block({ label, v, color }: { label: string; v: number; color: string }) {
  return (
    <div>
      <div className="text-[10px] mono uppercase tracking-[0.15em]"
        style={{ color }}>{label}</div>
      <div className="serif text-[28px] leading-none tabular font-light mt-1"
        style={{ color: "var(--ink)" }}>
        {(v * 100).toFixed(1)}<span className="text-[14px] opacity-50">%</span>
      </div>
    </div>
  );
}

function Mini({ label, v }: { label: string; v: number }) {
  return (
    <div>
      <div className="text-[10px] mono uppercase tracking-[0.15em]"
        style={{ color: "var(--ink-4)" }}>{label}</div>
      <div className="mono text-[16px] tabular mt-0.5" style={{ color: "var(--ink-2)" }}>
        {(v * 100).toFixed(1)}%
      </div>
    </div>
  );
}
