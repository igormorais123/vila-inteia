"""
Teste: Prompt RICO (10 técnicas Helena Master) vs Prompt Genérico.
Compara qualidade de resposta do Eduardo Cunha (persona que recusava antes).
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["OMNIROUTE_URL"] = "https://api.inteia.com.br/api/v1/vila-inteia/chat"
os.environ["OMNIROUTE_API_KEY"] = "dummy"

from engine.ia_client import chamar_llm_conversa
from engine.persona import Persona

# Carregar Eduardo Cunha
with open("data/banco-consultores-lendarios.json", encoding="utf-8") as f:
    consultores = json.load(f)

cunha_data = None
for c in consultores:
    if "Cunha" in c.get("nome_exibicao", ""):
        cunha_data = c
        break

if not cunha_data:
    print("Eduardo Cunha não encontrado nos consultores")
    sys.exit(1)

print(f"Consultor: {cunha_data['nome_exibicao']}")
print(f"Título: {cunha_data.get('titulo', '?')}")
print(f"Tier: {cunha_data.get('tier', '?')}")
print()

# Criar persona
cunha = Persona(dados_consultor=cunha_data)

# ── TESTE 1: Prompt GENÉRICO (antigo) ──
print("=" * 70)
print("  TESTE 1: PROMPT GENÉRICO (como era antes)")
print("=" * 70)

system_old = (
    f"Você é {cunha.nome_exibicao}. {cunha_data.get('titulo', '')}. "
    f"{cunha_data.get('personalidade_resumo', '')} "
    f"Responda com sua perspectiva UNICA."
)
user_old = (
    'PESQUISA PROFUNDA sobre: "IA vai substituir advogados no Brasil ate 2030"\n\n'
    'Responda em 3-4 frases. Inclua: (1) sua analise, '
    '(2) um dado ou referencia concreta, (3) uma pergunta que aprofunde.'
)

print(f"\nSystem ({len(system_old)} chars):")
print(f"  {system_old[:100]}...")
print(f"\nUser ({len(user_old)} chars)")

resp1 = chamar_llm_conversa(system_old, user_old, modelo="BestFREE", max_tokens=300)
print(f"\nRESPOSTA ({len(resp1 or '')} chars):")
print(resp1 or "[VAZIO/RECUSOU]")
print()

# ── TESTE 2: Prompt RICO (Helena Master — 10 técnicas) ──
print("=" * 70)
print("  TESTE 2: PROMPT RICO (Helena Master — 10 técnicas)")
print("=" * 70)

system_new, user_new = cunha.gerar_prompt_pesquisa(
    tema="IA vai substituir advogados no Brasil ate 2030",
    tipo="pesquisa",
)

print(f"\nSystem ({len(system_new)} chars) — {len(system_new.split(chr(10)))} linhas")
print(f"User ({len(user_new)} chars)")

resp2 = chamar_llm_conversa(system_new, user_new, modelo="BestFREE", max_tokens=400)
print(f"\nRESPOSTA ({len(resp2 or '')} chars):")
print(resp2 or "[VAZIO/RECUSOU]")
print()

# ── COMPARAÇÃO ──
print("=" * 70)
print("  COMPARAÇÃO")
print("=" * 70)
print(f"  Genérico: {len(system_old):>5} chars system | {len(resp1 or ''):>4} chars resposta")
print(f"  Rico:     {len(system_new):>5} chars system | {len(resp2 or ''):>4} chars resposta")
print(f"  Recusou genérico: {'SIM' if not resp1 or 'recuso' in (resp1 or '').lower() else 'NÃO'}")
print(f"  Recusou rico:     {'SIM' if not resp2 or 'recuso' in (resp2 or '').lower() else 'NÃO'}")
