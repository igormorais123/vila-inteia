"""Testes Ondas 46-48."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from pathlib import Path
from engine.auth import RateLimiter, auth_ativa, config_resumo
from engine.notifier import Notifier, NotificacaoRegistro

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


# ========== Onda 46 ==========

def t_rate_limiter_permite_dentro_limite():
    rl = RateLimiter(limite_por_min=10)
    for i in range(10):
        ok_flag, rest = rl.permitir("1.2.3.4")
        if not ok_flag:
            teste(f"rate limiter permite {i+1}/10", False, f"bloqueou cedo")
            return
    teste("rate limiter permite 10 requests", True)


def t_rate_limiter_bloqueia_excesso():
    rl = RateLimiter(limite_por_min=3)
    for _ in range(3):
        rl.permitir("5.5.5.5")
    ok_flag, _ = rl.permitir("5.5.5.5")
    teste("rate limiter bloqueia 4º request", not ok_flag)


def t_rate_limiter_ip_independente():
    rl = RateLimiter(limite_por_min=2)
    rl.permitir("a"); rl.permitir("a")
    ok_flag, _ = rl.permitir("a")
    teste("a: 3º bloqueado", not ok_flag)
    ok_flag, _ = rl.permitir("b")
    teste("b: 1º permitido (IP independente)", ok_flag)


def t_config_resumo_campos():
    r = config_resumo()
    teste("config tem auth_ativa", "auth_ativa" in r)
    teste("config tem rate_limit_per_min", "rate_limit_per_min" in r)
    teste("config tem paths_excluidos", "paths_excluidos" in r)


# ========== Onda 47 ==========

def t_backup_script_existe():
    teste("scripts/vila_backup.py existe",
          Path("scripts/vila_backup.py").exists())


def t_backup_script_parsea():
    import ast
    try:
        ast.parse(Path("scripts/vila_backup.py").read_text())
        teste("backup parsea Python", True)
    except SyntaxError as e:
        teste("backup parsea", False, str(e))


def t_backup_script_subcmds():
    import subprocess
    r = subprocess.run(
        ["python", "scripts/vila_backup.py", "--help"],
        capture_output=True, text=True, timeout=5,
    )
    teste("backup --help retorna 0", r.returncode == 0)
    teste("backup menciona dump", "dump" in r.stdout)
    teste("backup menciona restore", "restore" in r.stdout)
    teste("backup menciona list", "list" in r.stdout)


# ========== Onda 48 ==========

def t_notifier_sem_webhook_inativo():
    n = Notifier(webhook_url="")
    teste("notifier sem webhook: ativo=False", not n.ativo)
    r = n.enviar("teste", "mensagem")
    teste("envio sem webhook retorna sucesso=False", not r.sucesso)


def t_notifier_registra_historico():
    n = Notifier(webhook_url="")
    n.enviar("a", "m1"); n.enviar("b", "m2")
    s = n.stats()
    teste("histórico registrado", s["total_enviadas"] == 2)


def t_notifier_anti_flood():
    n = Notifier(webhook_url="")
    n._min_intervalo_s = 100  # força bloqueio
    n.enviar("repetido", "primeira")
    r2 = n.enviar("repetido", "segunda")
    # Segunda bloqueada pelo anti-flood
    teste("anti-flood bloqueia 2ª chamada mesmo tipo",
          not r2.sucesso and r2.mensagem == "segunda")


def t_notifier_formato_slack():
    n = Notifier(webhook_url="http://x", formato="slack")
    p = n._formatar_payload("oi")
    teste("slack: {text: ...}", p == {"text": "oi"})


def t_notifier_formato_discord():
    n = Notifier(webhook_url="http://x", formato="discord")
    p = n._formatar_payload("oi")
    teste("discord: {content: ...}", p == {"content": "oi"})


def t_notifier_notificar_mule():
    n = Notifier(webhook_url="")
    r = n.notificar_mule({"z_score": 3.5, "descricao": "anomalia X"}, step=42)
    teste("notificar_mule formata mensagem",
          "step 42" in r.mensagem and "z=3.5" in r.mensagem)


def main():
    print("=== test_ondas_46_48 ===")
    for fn in [t_rate_limiter_permite_dentro_limite, t_rate_limiter_bloqueia_excesso,
               t_rate_limiter_ip_independente, t_config_resumo_campos,
               t_backup_script_existe, t_backup_script_parsea, t_backup_script_subcmds,
               t_notifier_sem_webhook_inativo, t_notifier_registra_historico,
               t_notifier_anti_flood, t_notifier_formato_slack, t_notifier_formato_discord,
               t_notifier_notificar_mule]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
