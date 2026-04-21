"""Testes Onda 103: auth + rate limit."""

from __future__ import annotations
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.auth_middleware import (
    auth_required, rate_limit, _keys_validas, _HISTORY,
)
from fastapi import HTTPException

ok, fail = 0, 0


def teste(nome, cond, det=""):
    global ok, fail
    if cond: ok += 1; print(f"  OK  {nome}")
    else:    fail += 1; print(f"  FAIL {nome} {det}")


class _FakeRequest:
    def __init__(self, headers=None, host="1.2.3.4"):
        self.headers = {k.lower(): v for k, v in (headers or {}).items()}
        class _C: pass
        self.client = _C(); self.client.host = host


def _reset_env():
    os.environ["VILA_API_KEYS"] = ""
    os.environ["VILA_RATE_LIMIT_RPM"] = "30"
    _HISTORY.clear()


def t_auth_off_quando_keys_vazio():
    _reset_env()
    req = _FakeRequest()
    try:
        auth_required(req)
        teste("auth off: no-op", True)
    except HTTPException:
        teste("auth off: no-op", False, "raised")


def t_auth_exige_header_quando_keys_setado():
    _reset_env()
    os.environ["VILA_API_KEYS"] = "secret-a,secret-b"
    req = _FakeRequest()
    try:
        auth_required(req)
        teste("sem header → 401", False, "did not raise")
    except HTTPException as e:
        teste("sem header → 401", e.status_code == 401)


def t_auth_aceita_header_valido():
    _reset_env()
    os.environ["VILA_API_KEYS"] = "secret-a,secret-b"
    req = _FakeRequest(headers={"X-API-Key": "secret-a"})
    try:
        auth_required(req)
        teste("header válido passa", True)
    except HTTPException:
        teste("header válido passa", False)


def t_auth_rejeita_invalido():
    _reset_env()
    os.environ["VILA_API_KEYS"] = "secret-a"
    req = _FakeRequest(headers={"X-API-Key": "bogus"})
    try:
        auth_required(req)
        teste("inválido → 401", False)
    except HTTPException as e:
        teste("inválido → 401", e.status_code == 401)


def t_rate_limit_permite_ate_limit():
    _reset_env()
    os.environ["VILA_RATE_LIMIT_RPM"] = "5"
    req = _FakeRequest(host="9.9.9.9")
    for _ in range(5):
        rate_limit(req)  # não raise
    teste("5 calls permitidas", True)
    try:
        rate_limit(req)
        teste("6ª call deveria 429", False)
    except HTTPException as e:
        teste("6ª call → 429", e.status_code == 429)


def t_rate_limit_ip_separado():
    _reset_env()
    os.environ["VILA_RATE_LIMIT_RPM"] = "2"
    r1 = _FakeRequest(host="1.1.1.1")
    r2 = _FakeRequest(host="2.2.2.2")
    rate_limit(r1); rate_limit(r1)
    rate_limit(r2); rate_limit(r2)
    teste("IPs isolados 2+2 OK", True)


def t_rate_limit_zero_disabled():
    _reset_env()
    os.environ["VILA_RATE_LIMIT_RPM"] = "0"
    req = _FakeRequest()
    for _ in range(100):
        rate_limit(req)
    teste("rpm=0 desabilita", True)


def main():
    print("=== test_auth_middleware ===")
    for fn in [t_auth_off_quando_keys_vazio, t_auth_exige_header_quando_keys_setado,
               t_auth_aceita_header_valido, t_auth_rejeita_invalido,
               t_rate_limit_permite_ate_limit, t_rate_limit_ip_separado,
               t_rate_limit_zero_disabled]:
        try: fn()
        except Exception as e:
            global fail; fail += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
            import traceback; traceback.print_exc()
    print(f"\n{ok} ok, {fail} fail")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
