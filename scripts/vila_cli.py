#!/usr/bin/env python3
"""
vila-cli — ferramenta de linha de comando para consultar Vila INTEIA
rodando em modo live.

Onda 30.

Uso:
    python scripts/vila_cli.py --url http://localhost:8100 trajetoria
    python scripts/vila_cli.py --url ... recomendacao
    python scripts/vila_cli.py --url ... calibrar --metodo laplace
    python scripts/vila_cli.py --url ... backtest --dataset tiktok_viral_2024
    python scripts/vila_cli.py --url ... export-run --arquivo /tmp/run.json
    python scripts/vila_cli.py --url ... mules
    python scripts/vila_cli.py --url ... stats
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.error


def _http(method: str, url: str, body: dict | None = None, timeout: int = 30):
    headers = {"Accept": "application/json"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", errors="ignore")[:300]
        return {"erro": f"HTTP {e.code}: {corpo}"}
    except urllib.error.URLError as e:
        return {"erro": f"URL error: {e.reason}"}


def cmd_trajetoria(base_url: str, args):
    r = _http("GET", f"{base_url}/api/v1/psicohistoria/trajetoria-atual?janela={args.janela}")
    print(json.dumps(r, indent=2, ensure_ascii=False))


def cmd_recomendacao(base_url: str, args):
    r = _http("GET", f"{base_url}/api/v1/psicohistoria/recomendacao")
    print(f"Estado atual:     {r.get('estado_atual', '—')}")
    print(f"Destino:          {r.get('destino_previsto', '—')}")
    print(f"Urgência:         {r.get('urgencia', '—')}")
    print(f"Ação recomendada: {r.get('acao_recomendada', '—')}")
    print(f"\n{r.get('justificativa', '')}")


def cmd_calibrar(base_url: str, args):
    r = _http("POST", f"{base_url}/api/v1/psicohistoria/calibrar",
               {"metodo": args.metodo, "alpha": args.alpha})
    if r.get("erro"):
        print(f"Erro: {r['erro']}")
        sys.exit(1)
    print(f"Transições:            {r.get('n_transicoes', 0)}")
    print(f"Cobertura:             {r.get('cobertura_pct', 0):.1f}%")
    print(f"Perplexity original:   {r.get('perplexity_original', 0):.3f}")
    print(f"Perplexity calibrada:  {r.get('perplexity_calibrada', 0):.3f}")
    orig = r.get('perplexity_original', 0)
    if orig > 0:
        ganho = (orig - r.get('perplexity_calibrada', 0)) / orig * 100
        print(f"Ganho:                 {ganho:.1f}%")


def cmd_backtest(base_url: str, args):
    r = _http("GET", f"{base_url}/api/v1/backtest/rodar/{args.dataset}")
    if r.get("erro"):
        print(f"Erro: {r['erro']}"); sys.exit(1)
    print(f"Dataset:  {r.get('dataset', '—')}")
    print(f"N eventos: {r.get('n_eventos', 0)}")
    print(f"Brier:     {r.get('brier', 0):.4f}")
    print(f"Log-loss:  {r.get('log_loss', 0):.4f}")
    print(f"Accuracy:  {r.get('accuracy', 0)*100:.1f}%")


def cmd_export_run(base_url: str, args):
    r = _http("GET", f"{base_url}/api/v1/psicohistoria/trajetoria-atual?janela=10000")
    meta = _http("GET", f"{base_url}/api/v1/psicohistoria/divergencia-atual")
    payload = {"trajetoria": r, "divergencia": meta}
    with open(args.arquivo, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Exportado: {args.arquivo}")
    print(f"Steps:     {r.get('n_steps_rastreados', 0)}")


def cmd_mules(base_url: str, args):
    r = _http("GET", f"{base_url}/api/v1/psicohistoria/mules-detectados")
    print(f"Total de Mules: {r.get('n_mules', 0)}")
    for m in r.get("mules_recentes", [])[:10]:
        print(f"  passo {m.get('passo', '?')}: z={m.get('z_score', 0):.2f}")


def cmd_stats(base_url: str, args):
    persist = _http("GET", f"{base_url}/api/v1/psicohistoria/persistencia/stats")
    traj = _http("GET", f"{base_url}/api/v1/psicohistoria/trajetoria-atual?janela=1")
    print("=== Vila Stats ===")
    print(f"Steps rastreados:    {traj.get('n_steps_rastreados', 0)}")
    print(f"Último estado:       {traj.get('ultimo_estado', '—')}")
    print(f"Persistência buffer: {persist.get('buffer_atual', 0)}")
    print(f"Total flushed:       {persist.get('total_flushed', 0)}")
    print(f"Supabase ativo:      {'sim' if persist.get('supabase_ativo') else 'não'}")


def cmd_comparativo(base_url: str, args):
    r = _http("GET", f"{base_url}/api/v1/psicohistoria/backtest-comparativo")
    print(f"Datasets avaliados: {r.get('n_datasets', 0)}")
    print(f"{'Dataset':<35} {'N':>4} {'Brier':>8} {'Acc':>7}")
    print("-" * 60)
    for d in r.get("resultados", []):
        if d.get("erro"):
            print(f"{d['dataset']:<35} ERRO: {d['erro']}")
            continue
        print(f"{d['dataset']:<35} {d['n_eventos']:>4} {d['brier']:>8.4f} {d['accuracy']*100:>6.1f}%")


def main():
    ap = argparse.ArgumentParser(description="vila-cli — CLI para Vila INTEIA")
    ap.add_argument("--url", default="http://localhost:8100", help="URL base da Vila")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_traj = sub.add_parser("trajetoria", help="Trajetória atual")
    p_traj.add_argument("--janela", type=int, default=100)

    sub.add_parser("recomendacao", help="Recomendação estratégica (Helena)")
    sub.add_parser("mules", help="Mules detectados")
    sub.add_parser("stats", help="Stats gerais")
    sub.add_parser("comparativo", help="Backtest comparativo")

    p_cal = sub.add_parser("calibrar", help="Calibra matriz")
    p_cal.add_argument("--metodo", default="laplace", choices=["mle", "laplace", "ewma"])
    p_cal.add_argument("--alpha", type=float, default=0.1)

    p_bt = sub.add_parser("backtest", help="Roda backtest dataset")
    p_bt.add_argument("--dataset", required=True)

    p_ex = sub.add_parser("export-run", help="Exporta run atual em JSON")
    p_ex.add_argument("--arquivo", required=True)

    args = ap.parse_args()
    cmd_map = {
        "trajetoria": cmd_trajetoria,
        "recomendacao": cmd_recomendacao,
        "calibrar": cmd_calibrar,
        "backtest": cmd_backtest,
        "export-run": cmd_export_run,
        "mules": cmd_mules,
        "stats": cmd_stats,
        "comparativo": cmd_comparativo,
    }
    cmd_map[args.cmd](args.url, args)


if __name__ == "__main__":
    main()
