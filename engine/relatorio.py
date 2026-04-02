"""
Motor de Relatório Executivo da Vila INTEIA.

Gera relatórios estratégicos consolidados a cada N steps.
O dono recebe CONCLUSÕES, não dados brutos.
"""

from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class RelatorioExecutivo:
    """Relatório estratégico consolidado."""
    periodo: str
    step: int
    hora_simulacao: str
    total_conversas: int
    total_sinteses: int
    total_posts: int

    conclusoes: list[str] = field(default_factory=list)
    divergencias: list[str] = field(default_factory=list)
    descobertas: list[str] = field(default_factory=list)
    recomendacoes: list[str] = field(default_factory=list)
    tendencias: list[str] = field(default_factory=list)
    proximos_passos: list[str] = field(default_factory=list)
    gerado_em: str = ""

    def __post_init__(self):
        if not self.gerado_em:
            self.gerado_em = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        return {
            "periodo": self.periodo,
            "step": self.step,
            "hora_simulacao": self.hora_simulacao,
            "stats": {
                "conversas": self.total_conversas,
                "sinteses": self.total_sinteses,
                "posts": self.total_posts,
            },
            "conclusoes": self.conclusoes,
            "divergencias": self.divergencias,
            "descobertas": self.descobertas,
            "recomendacoes": self.recomendacoes,
            "tendencias": self.tendencias,
            "proximos_passos": self.proximos_passos,
            "gerado_em": self.gerado_em,
        }

    def to_markdown(self) -> str:
        md = f"""# Relatório Executivo Vila INTEIA — {self.periodo}
**Step {self.step}** | {self.hora_simulacao} | Gerado em {self.gerado_em}
**{self.total_conversas} conversas** | **{self.total_sinteses} sínteses** | **{self.total_posts} posts**

---

## Conclusões Principais
{chr(10).join(f'- {c}' for c in self.conclusoes) or '- Nenhuma conclusão ainda (aguardando mais steps)'}

## Divergências Produtivas
{chr(10).join(f'- {d}' for d in self.divergencias) or '- Sem divergências significativas'}

## Descobertas do Autoresearch
{chr(10).join(f'- {d}' for d in self.descobertas) or '- Autoresearch ainda não executou'}

## Recomendações (O QUE FAZER AGORA)
{chr(10).join(f'{i+1}. {r}' for i, r in enumerate(self.recomendacoes)) or '1. Aguardar mais dados'}

## Tendências Detectadas
{chr(10).join(f'- {t}' for t in self.tendencias) or '- Aguardando 50+ steps para detectar padrões'}

## Próximos Passos
{chr(10).join(f'→ {p}' for p in self.proximos_passos)}

---
*Gerado automaticamente pela Vila INTEIA — {self.total_conversas} conversas entre 151 consultores lendários*
"""
        return md


def gerar_relatorio(simulacao) -> RelatorioExecutivo:
    """Gera relatório executivo consolidado da simulação."""
    from . import previsibilidade as prev_module

    # Coletar conclusões das sínteses
    conclusoes = []
    divergencias = []
    recomendacoes_coletadas = []

    for s in simulacao.sinteses[-20:]:
        sint_texto = s.get("sintese", "")
        # Extrair linhas que começam com CONCLUSÃO
        for linha in sint_texto.split("\n"):
            if linha.startswith("CONCLUSÃO"):
                conclusoes.append(linha)
            elif "DIVERGÊNCIA" in linha or "ALERTA" in linha:
                divergencias.append(linha.replace("DIVERGÊNCIAS: ", ""))

        for r in s.get("recomendacoes", []):
            if r not in recomendacoes_coletadas:
                recomendacoes_coletadas.append(r)

    # Descobertas do autoresearch
    descobertas = []
    for desc in simulacao.motor_autoresearch.descobertas[-5:]:
        if desc and "inconclusiva" not in desc.lower():
            descobertas.append(desc[:200])

    # Tendências
    tendencias_obj = simulacao.motor_previsibilidade.analisar_tendencias()
    tendencias = [
        f"{t.topico} ({t.direcao}, força {t.forca:.0%}) — {t.previsao}"
        for t in tendencias_obj[:5]
    ]

    # Próximos passos
    proximos = []
    sugestao = simulacao.motor_previsibilidade.sugerir_proximo_topico(
        getattr(simulacao, '_config_topicos', [])
    )
    if sugestao:
        proximos.append(f"Injetar tópico sugerido: '{sugestao}'")
    if not descobertas:
        proximos.append("Autoresearch ativa no step 100 — aguardar para primeiras descobertas")
    if len(conclusoes) < 3:
        proximos.append(f"Mais {max(0, 30 - simulacao.step)} steps até volume de dados suficiente")
    proximos.append("Monitorar divergências — onde há debate há insight")

    return RelatorioExecutivo(
        periodo=f"Steps 1-{simulacao.step}",
        step=simulacao.step,
        hora_simulacao=simulacao.hora_atual.strftime("%Y-%m-%d %H:%M"),
        total_conversas=simulacao.stats.get("total_conversas", 0),
        total_sinteses=simulacao.stats.get("total_sinteses", 0),
        total_posts=simulacao.rede_social.total_posts,
        conclusoes=conclusoes[:5],
        divergencias=divergencias[:5],
        descobertas=descobertas[:3],
        recomendacoes=recomendacoes_coletadas[:5],
        tendencias=tendencias,
        proximos_passos=proximos,
    )
