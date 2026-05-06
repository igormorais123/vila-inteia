#!/usr/bin/env python3
"""Smoke test: verify political-prediction stack end-to-end.

Runs without the API server (uses TestClient) so it works in CI.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.rotas_politica import router

app = FastAPI()
app.include_router(router)
c = TestClient(app)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name} {detail}")


print("== smoke test political API ==\n")

# 1. health
r = c.get("/api/v1/politica/health")
check("health 200", r.status_code == 200)
h = r.json()
check("health has snapshot",   h.get("snapshot_predicted_at") is not None)
check("health n_train > 0",    (h.get("n_train_events") or 0) > 0)

# 2. elections
r = c.get("/api/v1/politica/elections")
check("elections 200", r.status_code == 200)
e = r.json()
check("elections cargos",      "presidente" in e["cargos_supported"])
check("elections >= 9 UFs",    len(e["ufs_covered"]) >= 9)

# 3. presidente
r = c.get("/api/v1/politica/predictions/presidente")
check("presidente 200", r.status_code == 200)
p = r.json()
check("presidente has >=5 cand", len(p["candidates"]) >= 5)  # Bolsonaro filtered ineligible
total = sum(c["p_winner"] for c in p["candidates"])
check("p_winner sums ~1",      abs(total - 1.0) < 0.01, f"got {total:.4f}")
check("Lula in top 1",         p["candidates"][0]["registry_id"] == "lula_2026")

# 4. governador
r = c.get("/api/v1/politica/predictions/governador?uf=SP")
check("governador SP 200",     r.status_code == 200)
g = r.json()
check("SP has 2 candidatos",   len(g["candidates"]) == 2)
sp_winner = max(g["candidates"], key=lambda x: x["p_winner"])
check("SP top = Tarcísio",     "Tarc" in sp_winner["nome"])

# 5. senador
r = c.get("/api/v1/politica/predictions/senador")
check("senador 200",            r.status_code == 200)
check("senador >= 4",           len(r.json()["candidates"]) >= 4)

# 6. custom predict
r = c.post("/api/v1/politica/predict", json={
    "cargo": "governador", "poll_lead_pp": 10, "days_to_election": 30,
    "incumbente": 1, "regime": "right",
})
check("custom predict 200",     r.status_code == 200)
data = r.json()
check("predict has p_blend",    "p_blend" in data)
check("predict p_blend > 0.5",  data["p_blend"] > 0.5, f"got {data.get('p_blend')}")

# 7. backtest
r = c.get("/api/v1/politica/backtest")
check("backtest 200",           r.status_code == 200)
bt = r.json()
check("backtest has selective", "selective_sweep" in bt)

# 8. predict edge: heavy underdog
r = c.post("/api/v1/politica/predict", json={
    "cargo": "presidente", "poll_lead_pp": -25, "days_to_election": 7,
    "incumbente": 0, "regime": "left",
})
data = r.json()
check("underdog low p_blend",   data["p_blend"] < 0.20, f"got {data['p_blend']}")

# 9. auth: anonymous still works under free tier
r = c.post("/api/v1/politica/predict", json={
    "cargo": "presidente", "poll_lead_pp": 0, "days_to_election": 30,
    "incumbente": 0, "regime": "center",
})
check("anon predict ok",        r.status_code == 200)

# 10. admin endpoints require token
r = c.post("/api/v1/politica/admin/keys/issue", json={"name": "x", "tier": "free"})
check("admin no token = 403",   r.status_code == 403)

# 11. admin issue with token
import os as _os
_os.environ["VILA_ADMIN_TOKEN"] = "test_token_123"
# reload module to pick up env
import importlib, api.rotas_politica as _rp
importlib.reload(_rp)
app2 = FastAPI()
app2.include_router(_rp.router)
c2 = TestClient(app2)
r = c2.post("/api/v1/politica/admin/keys/issue",
            json={"name": "smoke_client", "tier": "pro"},
            headers={"X-Admin-Token": "test_token_123"})
check("admin issue ok",         r.status_code == 200)
issued = r.json().get("api_key", "")
check("issued key prefix",      issued.startswith("vila_pol_"))

# 12. /me endpoint
r = c2.get("/api/v1/politica/me", headers={"X-API-Key": issued})
check("me ok",                  r.status_code == 200 and r.json()["tier"] == "pro")

# 13. invalid key = 401
r = c2.get("/api/v1/politica/me", headers={"X-API-Key": "vila_pol_invalid"})
check("invalid key = 401",      r.status_code == 401)

# 14. revoke
r = c2.post(f"/api/v1/politica/admin/keys/revoke?api_key={issued}",
            headers={"X-Admin-Token": "test_token_123"})
check("revoke ok",              r.status_code == 200)
r = c2.get("/api/v1/politica/me", headers={"X-API-Key": issued})
check("revoked = 401",          r.status_code == 401)

print(f"\n== {passed} passed, {failed} failed ==")
sys.exit(0 if failed == 0 else 1)
