"""Testes Ondas 55-57."""

from __future__ import annotations
import sys, os, json, subprocess, tempfile, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
from pathlib import Path

from engine.log_estruturado import (
    StructuredFormatter, configurar, configurar_arquivo, log_evento,
)
from engine.psicohistoria.genetic_tuner import (
    evoluir, fitness_individuo, _aleatorizar, _valido,
)
from engine.psicohistoria.detector_estado_vila import MetricasStep
from engine.psicohistoria.tuner_classificador import ThresholdsClassificador

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# Onda 55

def t_formatter_emite_json():
    f = StructuredFormatter()
    rec = logging.LogRecord(
        "test", logging.INFO, "/path", 42, "hello %s", ("world",), None,
    )
    out = f.format(rec)
    data = json.loads(out)
    teste("formatter JSON válido", isinstance(data, dict))
    teste("level preservado", data["level"] == "INFO")
    teste("message expandida", data["message"] == "hello world")
    teste("linha preservada", data["line"] == 42)


def t_formatter_inclui_extras():
    f = StructuredFormatter()
    rec = logging.LogRecord(
        "test", logging.INFO, "/path", 1, "x", (), None,
    )
    rec.step = 42
    rec.estado = "expansao"
    data = json.loads(f.format(rec))
    teste("extras preservados: step", data.get("step") == 42)
    teste("extras preservados: estado", data.get("estado") == "expansao")


def t_formatter_extra_defaults():
    f = StructuredFormatter(extra_defaults={"service": "vila"})
    rec = logging.LogRecord(
        "x", logging.INFO, "/p", 1, "m", (), None,
    )
    data = json.loads(f.format(rec))
    teste("extra_default injetado", data.get("service") == "vila")


def t_configurar_stream():
    buf = io.StringIO()
    root = configurar(level="DEBUG", extra_defaults={"vila": "test"}, stream=buf)
    root.info("teste msg", extra={"foo": "bar"})
    buf.seek(0)
    linhas = [l for l in buf.getvalue().split("\n") if l.strip()]
    teste("emitiu pelo menos 1 linha", len(linhas) >= 1)
    if linhas:
        data = json.loads(linhas[0])
        teste("level INFO", data["level"] == "INFO")
        teste("extra_default presente", data.get("vila") == "test")


def t_configurar_arquivo():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        root = configurar_arquivo(f.name, level="INFO")
        root.info("test file")
        # Flush
        for h in root.handlers:
            h.flush()
        conteudo = Path(f.name).read_text()
        teste("arquivo recebe logs", len(conteudo) > 0)
        linhas = [l for l in conteudo.split("\n") if l.strip()]
        teste("1 linha JSONL", len(linhas) == 1)
        if linhas:
            json.loads(linhas[0])
            teste("JSON válido no arquivo", True)
        os.unlink(f.name)


# Onda 56

def t_validador_existe():
    teste("validar_calibracao.py existe",
          Path("scripts/validar_calibracao.py").exists())


def t_validador_executa():
    r = subprocess.run(
        ["python", "scripts/validar_calibracao.py",
         "--n-steps", "500", "--metodo", "laplace", "--alpha", "0.1"],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    teste("validador rodou", r.returncode in (0, 1))
    teste("output menciona VEREDITO", "VEREDITO" in r.stdout)
    teste("output menciona Frobenius", "Frobenius" in r.stdout)


# Onda 57

def t_aleatorizar_produz_valido_eventualmente():
    import random
    rng = random.Random(1)
    validos = sum(_valido(_aleatorizar(rng)) for _ in range(50))
    teste("ao menos 1 de 50 é válido", validos > 0)


def t_fitness_individuo_vazio():
    t = ThresholdsClassificador()
    f = fitness_individuo(t, [])
    teste("fitness vazio = 0", f == 0.0)


def t_evoluir_melhora_fitness():
    # 50 métricas diversificadas
    metricas = []
    for i in range(50):
        m = MetricasStep(
            step=i, n_conversas=i, n_reflexoes=i % 3,
            n_agentes_ativos=50 + i % 30,
            n_agentes_latentes=50 - i % 30,
            total_agentes=100,
            polarizacao_media=(i % 5) / 5,
            gini_economia=(i % 3) * 0.3,
            contribuicoes_ao_desafio=i % 30,
        )
        metricas.append(m)
    r = evoluir(metricas, pop_size=10, geracoes=15, seed=1)
    teste("GA roda 15 gerações",
          r.geracoes == 15 and len(r.historico_fitness) == 16)
    teste("fitness final >= inicial",
          r.historico_fitness[-1] >= r.historico_fitness[0])


def t_evoluir_melhor_valido():
    metricas = [MetricasStep(step=i, n_conversas=5, n_reflexoes=1,
                               n_agentes_ativos=80, n_agentes_latentes=20,
                               total_agentes=100,
                               polarizacao_media=0.2,
                               gini_economia=0.3,
                               contribuicoes_ao_desafio=i)
                for i in range(20)]
    r = evoluir(metricas, pop_size=8, geracoes=10, seed=2)
    teste("melhor tem thresholds válidos", _valido(r.melhor.thresholds))


def main():
    print("=== test_ondas_55_57 ===")
    for fn in [t_formatter_emite_json, t_formatter_inclui_extras,
               t_formatter_extra_defaults, t_configurar_stream, t_configurar_arquivo,
               t_validador_existe, t_validador_executa,
               t_aleatorizar_produz_valido_eventualmente, t_fitness_individuo_vazio,
               t_evoluir_melhora_fitness, t_evoluir_melhor_valido]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
