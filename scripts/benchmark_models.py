#!/usr/bin/env python3
"""
Onda 91: benchmark Groq free-tier models.

Teste cada modelo com prompt fixo, mede latência, tokens, custo, taxa erro.
Compara qualidade (len + heurística).

Uso:
    python scripts/benchmark_models.py
    python scripts/benchmark_models.py --prompt "custom pergunta"
    python scripts/benchmark_models.py --models llama-3.1-8b-instant,...
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Modelos Groq free tier candidatos (April 2026)
MODELOS_DEFAULT = [
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "moonshotai/kimi-k2-instruct",
    "deepseek-r1-distill-llama-70b",
    "mistral-saba-24b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "allam-2-7b",
    "compound-beta",
    "compound-beta-mini",
]

PROMPT_DEFAULT = (
    "Você é Elon Musk. Em 3-4 frases em PT-BR autêntico, "
    "responda: Por que a humanidade precisa se tornar multi-planetária? "
    "Use suas expressões típicas."
)


def _carregar_env():
    """Load ~/.vila_env."""
    env_file = Path.home() / ".vila_env"
    if not env_file.exists():
        return
    for linha in env_file.read_text().splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def bench_um(modelo: str, prompt: str, timeout: int = 15) -> dict:
    from openai import OpenAI
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return {"modelo": modelo, "erro": "GROQ_API_KEY ausente"}
    client = OpenAI(
        api_key=key,
        base_url="https://api.groq.com/openai/v1",
        timeout=timeout,
    )
    t0 = time.monotonic()
    try:
        r = client.chat.completions.create(
            model=modelo,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7,
        )
        dt = (time.monotonic() - t0) * 1000
        resp = r.choices[0].message.content or ""
        u = r.usage
        return {
            "modelo": modelo,
            "latencia_ms": round(dt, 0),
            "tokens_in": u.prompt_tokens if u else None,
            "tokens_out": u.completion_tokens if u else None,
            "len_resposta": len(resp),
            "resposta_preview": resp[:200],
            "ok": True,
        }
    except Exception as e:
        dt = (time.monotonic() - t0) * 1000
        msg = str(e)
        tipo = type(e).__name__
        # Classificar erro comum
        if "rate_limit" in msg.lower() or "429" in msg:
            classe = "RATE_LIMIT"
        elif "not found" in msg.lower() or "does not exist" in msg.lower() or "404" in msg:
            classe = "NOT_FOUND"
        elif "decommissioned" in msg.lower():
            classe = "DECOMMISSIONED"
        elif "access" in msg.lower() or "403" in msg:
            classe = "NO_ACCESS"
        else:
            classe = "OUTRO"
        return {
            "modelo": modelo,
            "latencia_ms": round(dt, 0),
            "erro": msg[:200],
            "erro_classe": classe,
            "ok": False,
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default=PROMPT_DEFAULT)
    ap.add_argument("--models", default=",".join(MODELOS_DEFAULT),
                     help="CSV de modelos (ou 'default')")
    ap.add_argument("--timeout", type=int, default=15)
    ap.add_argument("--out", default=None, help="JSON output file")
    args = ap.parse_args()

    _carregar_env()

    modelos = [m.strip() for m in args.models.split(",") if m.strip()]
    print(f"# Benchmark Groq — {len(modelos)} modelos")
    print(f"# prompt: {args.prompt[:80]}...")
    print()

    resultados = []
    for m in modelos:
        print(f"→ {m}", end=" ", flush=True)
        r = bench_um(m, args.prompt, args.timeout)
        resultados.append(r)
        if r.get("ok"):
            print(f"  OK  {r['latencia_ms']:.0f}ms  {r['tokens_in']}→{r['tokens_out']}tok  {r['len_resposta']}ch")
        else:
            print(f"  FAIL [{r.get('erro_classe', '?')}]  {r.get('latencia_ms', 0):.0f}ms")

    print()
    # Ranking por latência (apenas OK)
    ok_res = sorted([r for r in resultados if r.get("ok")],
                     key=lambda x: x["latencia_ms"])
    if ok_res:
        print("## Ranking por latência (OK apenas)")
        for i, r in enumerate(ok_res, 1):
            print(f"  {i}. {r['modelo']:50s} {r['latencia_ms']:>6.0f}ms  {r['len_resposta']:>4}ch")
        print()
        print("## Preview melhor resposta (menor latência)")
        best = ok_res[0]
        print(f"### {best['modelo']}")
        print(best["resposta_preview"])
        print()

    # Resumo erros
    err_res = [r for r in resultados if not r.get("ok")]
    if err_res:
        print("## Erros")
        for r in err_res:
            print(f"  {r['modelo']:50s} [{r.get('erro_classe','?'):12s}] {r.get('erro','')[:80]}")

    if args.out:
        Path(args.out).write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
        print(f"\nJSON: {args.out}")


if __name__ == "__main__":
    main()
