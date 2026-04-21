"""Testes Onda 89: panel chat multi-persona paralelo."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.panel_chat import panel_chat
from engine.persona_chat import resetar_historico

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _MockPersona:
    def __init__(self, nome): self.nome_exibicao = nome
    def gerar_prompt_sistema(self): return f"Você é {self.nome_exibicao}."


class _MockSim:
    def __init__(self, personas): self.personas = personas


def _sim(n=3):
    resetar_historico()
    nomes = {"CL001":"Elon Musk", "CL002":"Steve Jobs", "CL003":"Warren Buffett"}
    return _MockSim({k: _MockPersona(v) for k,v in list(nomes.items())[:n]})


def t_persona_ids_vazio():
    out = panel_chat([], "x?", _sim(), llm_fn=lambda **k: "ok")
    teste("vazio: n_personas=0", out["n_personas"] == 0)
    teste("erro presente", "erro" in out)


def t_basico_3_personas():
    chamadas = []
    def mock(mensagens, modelo, max_tokens, temperatura, system_prompt="", bypass_step_cap=False):
        chamadas.append(system_prompt[:20])
        return f"resp para {system_prompt[:20]}"
    out = panel_chat(["CL001","CL002","CL003"], "como escalar?", _sim(3), llm_fn=mock)
    teste("n_personas=3", out["n_personas"] == 3)
    teste("3 respostas", len(out["respostas"]) == 3)
    teste("cada resposta não None",
          all(r["resposta"] for r in out["respostas"]))
    teste("latencia_total > 0", out["latencia_ms_total"] > 0)


def t_dedup_ordem_preservada():
    def mock(**k): return "ok"
    out = panel_chat(["CL001","CL002","CL001","CL003"], "?", _sim(3), llm_fn=mock)
    teste("dedup: 3 personas únicas", out["n_personas"] == 3)
    ids = [r["persona_id"] for r in out["respostas"]]
    teste("ordem preservada", ids == ["CL001","CL002","CL003"])


def t_persona_inexistente_propaga_erro():
    def mock(**k): return "ok"
    out = panel_chat(["CL001","CL999"], "?", _sim(3), llm_fn=mock)
    teste("2 personas tentadas", len(out["respostas"]) == 2)
    cl999 = next(r for r in out["respostas"] if r["persona_id"] == "CL999")
    teste("CL999 erro preserved", cl999.get("erro") is not None)
    cl001 = next(r for r in out["respostas"] if r["persona_id"] == "CL001")
    teste("CL001 ainda responde", cl001.get("resposta") == "ok")


def t_paralelo_mais_rapido_que_serial():
    import time
    def slow(**k):
        time.sleep(0.1)
        return "ok"
    sim = _sim(3)
    t0 = time.monotonic()
    panel_chat(["CL001","CL002","CL003"], "?", sim, llm_fn=slow, paralelo=False)
    tserial = time.monotonic() - t0

    t0 = time.monotonic()
    panel_chat(["CL001","CL002","CL003"], "?", sim, llm_fn=slow, paralelo=True)
    tparallel = time.monotonic() - t0

    teste(f"paralelo < serial ({tparallel*1000:.0f}ms < {tserial*1000:.0f}ms)",
          tparallel < tserial * 0.8)


def t_latencia_max_presente():
    def mock(**k): return "ok"
    out = panel_chat(["CL001"], "?", _sim(1), llm_fn=mock)
    teste("latencia_ms_max >= 0", out["latencia_ms_max"] >= 0)
    teste("latencia_ms_total >= latencia_ms_max",
          out["latencia_ms_total"] >= out["latencia_ms_max"])


def main():
    print("=== test_panel_chat ===")
    for fn in [t_persona_ids_vazio, t_basico_3_personas,
               t_dedup_ordem_preservada, t_persona_inexistente_propaga_erro,
               t_paralelo_mais_rapido_que_serial, t_latencia_max_presente]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
