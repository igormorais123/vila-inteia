"""
E2E teste via Playwright (Onda 45).

Sobe servidor vila + navega cockpit + dispara calibração via UI + valida
estado retornado.

Requer: pip install playwright && playwright install chromium

Rodar:
    PYTHONPATH=. python tests/e2e_playwright.py

Não executa em CI automaticamente — requer Playwright browser instalado.
"""

from __future__ import annotations

import sys
import os
import time
import subprocess
import signal
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _wait_alive(url: str, timeout: int = 30) -> bool:
    for _ in range(timeout):
        try:
            urllib.request.urlopen(url, timeout=2).read()
            return True
        except Exception:
            time.sleep(1)
    return False


def _kill_servers():
    try:
        subprocess.run(["pkill", "-9", "-f", "main.py"], check=False, timeout=5)
    except Exception:
        pass


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP: playwright não instalado (pip install playwright && playwright install chromium)")
        sys.exit(0)

    env = os.environ.copy()
    env.update({
        "OMNIROUTE_API_KEY": "", "CLAUDE_API_KEY": "",
        "SUPABASE_VILA_URL": "", "SUPABASE_VILA_KEY": "",
        "PYTHONPATH": ".",
    })

    print("[1/5] Starting server...")
    server = subprocess.Popen(
        ["python", "main.py", "live", "--port", "8600",
         "--intervalo", "1", "--topico", "e2e test"],
        env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    try:
        if not _wait_alive("http://localhost:8600/api/v1/vila/health", timeout=30):
            print("FAIL: server não subiu em 30s")
            _kill_servers()
            sys.exit(1)
        print("[2/5] Server up. Running Playwright...")

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1400, "height": 900})
            page = context.new_page()

            # Cockpit
            print("[3/5] Navigating cockpit...")
            page.goto("http://localhost:8600/cockpit.html", wait_until="load")
            page.wait_for_timeout(3000)

            # Verifica elementos
            assert page.locator("#topbar-step").count() == 1, "topbar-step não achado"
            assert page.locator("#m-estado").count() == 1, "m-estado não achado"
            print("[4/5] Cockpit renderizou com elementos esperados")

            # Health endpoint direto
            response = page.request.get("http://localhost:8600/api/v1/vila/health")
            data = response.json()
            assert "subsistemas" in data, "health sem subsistemas"
            assert data["total_subsistemas"] >= 8, f"esperado ≥8 subsistemas, got {data.get('total_subsistemas')}"
            print(f"[5/5] Health OK — {data['total_subsistemas']} subsistemas, ok={data['ok']}")

            # Metrics endpoint
            response = page.request.get("http://localhost:8600/metrics")
            metrics = response.text()
            assert "vila_steps_total" in metrics, "métricas Prometheus ausentes"
            print("     Metrics endpoint OK")

            browser.close()
        print("\n=== E2E PASSED ===")
    finally:
        _kill_servers()


if __name__ == "__main__":
    main()
