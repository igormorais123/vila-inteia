#!/usr/bin/env bash
# Script de fallback — commit + push da Onda 3+4 do HARNESS_VILA
# Gerado automaticamente. Executar se o agente Claude não conseguir
# completar o commit devido a problema de sandbox.
set -euo pipefail

cd "$(dirname "$0")/.."

git add -A
git status --short

git commit -m "feat(harness): Onda 3+4 MVP — skills canônicas, capability cards, Produto 1, Ficha do Fundador" \
  -m "Fecha fases finais do HARNESS_VILA.md aplicadas à Vila INTEIA." \
  -m "" \
  -m "Onda 3 (skills + protocolos):" \
  -m "  engine/harness/skill_registry.py — carrega SKILL.md authored + bootstrap automático de engine/oficinas.py. 23 skills totais (3 authored: laboratorio, torre_estrategia, tribunal + 20 bootstrapped). Progressive disclosure em 3 níveis. Busca semântica-lite." \
  -m "  engine/harness/protocolos/ — 3 capability cards MCP-like em TOML: omniroute.completar, mirante.publicar_materia, supabase.snapshot_vila. Parser stdlib (tomllib 3.11+)." \
  -m "  engine/skills_oficinas/<nome>/SKILL.md — 3 authored canonical files com frontmatter YAML + N2/N3 body." \
  -m "" \
  -m "Onda 4 MVP (Ficha do Fundador + Produto 1):" \
  -m "  engine/memoria/fundador.py — FichaFundador consolidada de ~/.claude/CLAUDE.md + ~/CLAUDE.md. Preferencias, neurocognicao (TDAH/TEA/AH), projetos ativos, restricoes operacionais, hierarquia de servico (Fundador->INTEIA->Colmeia->Cliente). Funcao ficha_para_injecao() para prompt ops." \
  -m "  POST /api/v1/harness/simular-decisao — Produto 1 MVP sincrono: recebe contexto+agentes+steps, descobre skills relevantes via registry, aplica orcamento, retorna relatorio com recomendacao, confianca e riscos." \
  -m "" \
  -m "Novas rotas:" \
  -m "  GET  /api/v1/harness/skills[?nivel=1|2|3]" \
  -m "  GET  /api/v1/harness/skills/buscar?q=termos" \
  -m "  GET  /api/v1/harness/skills/{nome}" \
  -m "  GET  /api/v1/harness/capabilities" \
  -m "  GET  /api/v1/harness/capabilities/{cap_id}" \
  -m "  GET  /api/v1/harness/fundador" \
  -m "  GET  /api/v1/harness/fundador/injecao" \
  -m "  POST /api/v1/harness/simular-decisao" \
  -m "" \
  -m "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"

git push origin main

echo "========================================"
echo "Commit + push concluidos."
echo "Aguarde ~2 min para Render re-buildar."
echo ""
echo "Verifique com:"
echo "  curl https://vila-inteia.onrender.com/api/v1/harness/saude"
echo "  curl https://vila-inteia.onrender.com/api/v1/harness/skills"
echo "  curl https://vila-inteia.onrender.com/api/v1/harness/capabilities"
echo "  curl https://vila-inteia.onrender.com/api/v1/harness/fundador"
echo "========================================"
