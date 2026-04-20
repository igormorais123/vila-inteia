"""
engine.proveniencia — proveniência cognitiva pública para matérias publicadas.

Onda 5. Permite que qualquer matéria publicada no Mirante News carregue um
trace_hash que expõe:
    - Quais agentes (habitantes) debateram o tópico
    - Cadeia causal completa (perceber → ... → sintetizar)
    - Custo em tokens/USD agregado
    - Tempo total de deliberação
    - Grafo de influência (quem citou quem)

Uso:
    from engine.proveniencia import construir_proveniencia, hash_trace
    prov = construir_proveniencia(materia_id, traces, agentes_envolvidos)
    h = hash_trace(prov)  # SHA-256 da cadeia inteira (não do conteúdo)
"""

from engine.proveniencia.construcao import (
    construir_proveniencia,
    Proveniencia,
    NoTrace,
    Influencia,
)
from engine.proveniencia.hash_helper import hash_trace, hash_materia

__all__ = [
    "construir_proveniencia",
    "Proveniencia",
    "NoTrace",
    "Influencia",
    "hash_trace",
    "hash_materia",
]
