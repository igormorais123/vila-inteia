"""Testes Onda 117: webhook alerts."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import webhook_alerts as wa

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


def _reset():
    wa.resetar_dedup()
    os.environ["VILA_WEBHOOK_URL"] = ""


def t_sem_url_nao_envia():
    _reset()
    r = wa.enviar_alerta("x", "titulo", "msg")
    teste("sem URL: sent=False", r["sent"] is False)
    teste("sem URL: ok=True (não é erro)", r["ok"] is True)


def t_dedup_mesma_categoria():
    _reset()
    os.environ["VILA_WEBHOOK_URL"] = "http://127.0.0.1:1"  # never connects
    r1 = wa.enviar_alerta("mule", "t", "m")  # Tenta enviar, falha connect
    r2 = wa.enviar_alerta("mule", "t", "m")
    teste("2ª chamada mesma cat: dedup", r2.get("dedup") is True)


def t_dedup_respeita_categorias_diferentes():
    _reset()
    os.environ["VILA_WEBHOOK_URL"] = "http://127.0.0.1:1"
    r1 = wa.enviar_alerta("mule", "t", "m")
    r2 = wa.enviar_alerta("circuit", "t", "m")
    teste("categoria diferente não dedup", r2.get("dedup") is not True)


def t_format_discord():
    p = wa._format_discord("Titulo", "Mensagem", cor=0xff0000)
    teste("discord tem embeds", "embeds" in p)
    teste("discord cor", p["embeds"][0]["color"] == 0xff0000)


def t_format_slack():
    p = wa._format_slack("Tit", "Msg", cor="danger")
    teste("slack tem attachments", "attachments" in p)
    teste("slack cor", p["attachments"][0]["color"] == "danger")


def t_format_generic():
    p = wa._format_generic("T", "M", extra_key="x")
    teste("generic tem titulo", p["titulo"] == "T")
    teste("generic tem extra", p.get("extra_key") == "x")


def t_alerta_mule_wrapper():
    _reset()
    r = wa.alerta_mule({"step": 42, "tipo": "spike"})
    teste("alerta_mule retorna dict", isinstance(r, dict))
    teste("alerta_mule sem URL: ok", r["ok"] is True)


def t_alerta_circuit_wrapper():
    _reset()
    r = wa.alerta_circuit_aberto("groq", 5)
    teste("alerta_circuit retorna dict", isinstance(r, dict))


def t_alerta_skill_neg():
    _reset()
    r = wa.alerta_skill_negativo(-0.5)
    teste("alerta_skill retorna dict", isinstance(r, dict))


def t_url_invalida_retorna_erro_sem_crash():
    _reset()
    os.environ["VILA_WEBHOOK_URL"] = "http://nao-existe-12345.invalid/hook"
    r = wa.enviar_alerta("x", "t", "m")
    teste("URL inválida não crasha", isinstance(r, dict))
    teste("URL inválida: sent=False", r.get("sent") is False)


def main():
    print("=== test_webhook_alerts ===")
    for fn in [t_sem_url_nao_envia, t_dedup_mesma_categoria,
               t_dedup_respeita_categorias_diferentes,
               t_format_discord, t_format_slack, t_format_generic,
               t_alerta_mule_wrapper, t_alerta_circuit_wrapper,
               t_alerta_skill_neg, t_url_invalida_retorna_erro_sem_crash]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
