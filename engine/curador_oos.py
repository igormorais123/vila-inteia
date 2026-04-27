"""
Onda 165: curador_oos — wrapper de curadoria para eventos pós-cutoff (OOS).

Aceita eventos curados manualmente (ou via mini) e aplica:
1. Validação Pydantic via EventoPreditivoV1.
2. Validação data_corte > CUTOFF_LLM (=2024-08-01 conservador para Llama-4).
3. Probe automático — se p_outcome_mean ≥ 0.65, marca leakage_risk=alto e
   audit_status=vetado_helena (entra em reserve, não em holdout).
4. Validação de fonte primária — pelo menos 1 FonteEvento em fonte_outcome
   com nivel='primaria' E data_acesso ≥ data_resolucao.
5. Hash SHA256 do evento congelado para reprodutibilidade.

Uso:
    from engine.curador_oos import curar_evento, curar_lote

    ev = EventoPreditivoV1(...)
    resultado = curar_evento(ev)
    # {'aprovado': True/False, 'razao': '...', 'evento': ev_atualizado, 'hash': '...'}
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from engine.eventos_v1 import EventoPreditivoV1, FonteEvento, to_jsonl
from engine.outcome_probe import (
    probar_evento, classificar_leakage,
    LEAKAGE_THRESHOLD_DEFAULT,
)

logger = logging.getLogger(__name__)


# Cutoff conservador para LLMs usados na Vila (Llama-4-scout, GPT-5.5).
# Eventos com data_corte_informacao < CUTOFF têm risco alto de memorização
# e são vetados por padrão.
CUTOFF_LLM = date(2024, 8, 1)


@dataclass
class ResultadoCuradoria:
    aprovado: bool
    razao: str
    evento: Optional[EventoPreditivoV1] = None
    hash_sha256: str = ""
    p_leakage: Optional[float] = None
    avisos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "aprovado": self.aprovado,
            "razao": self.razao,
            "hash": self.hash_sha256,
            "p_leakage": self.p_leakage,
            "avisos": self.avisos,
            "evento_id": self.evento.id if self.evento else None,
        }


def _hash_evento(ev: EventoPreditivoV1) -> str:
    """SHA256 do JSON canônico do evento (sem audit_status volátil)."""
    d = ev.model_dump(mode="json")
    # Remove campos que mudam durante curadoria
    for k in ("audit_status", "leakage_risk", "leakage_mitigations"):
        d.pop(k, None)
    payload = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _validar_cutoff(ev: EventoPreditivoV1) -> Optional[str]:
    """Retorna mensagem de erro se data_corte é anterior ao cutoff LLM."""
    if ev.data_corte_informacao < CUTOFF_LLM:
        return (f"data_corte_informacao={ev.data_corte_informacao} é anterior "
                f"ao CUTOFF_LLM={CUTOFF_LLM} — risco alto de memorização")
    return None


def _validar_fonte_primaria(ev: EventoPreditivoV1) -> Optional[str]:
    """Exige pelo menos 1 fonte primária de outcome com data_acesso ≥ data_resolucao."""
    primarias = [f for f in ev.fonte_outcome if f.nivel == "primaria"]
    if not primarias:
        return "fonte_outcome precisa de pelo menos 1 fonte com nivel='primaria'"
    com_data = [f for f in primarias
                if f.data_acesso is not None and f.data_acesso >= ev.data_resolucao]
    if not com_data:
        return ("fonte primária precisa ter data_acesso >= data_resolucao "
                "(prova que outcome foi resolvido por fonte oficial)")
    return None


def curar_evento(
    ev: EventoPreditivoV1,
    rodar_probe: bool = True,
    probe_kwargs: Optional[dict] = None,
) -> ResultadoCuradoria:
    """Aplica todos os checks. Retorna ResultadoCuradoria.

    Se rodar_probe=False, pula chamada ao LLM (útil para testes).
    """
    avisos: list[str] = []

    # Check 1: cutoff LLM
    erro_cutoff = _validar_cutoff(ev)
    if erro_cutoff:
        return ResultadoCuradoria(
            aprovado=False, razao=erro_cutoff, evento=ev,
            hash_sha256=_hash_evento(ev),
        )

    # Check 2: fonte primária
    erro_fonte = _validar_fonte_primaria(ev)
    if erro_fonte:
        return ResultadoCuradoria(
            aprovado=False, razao=erro_fonte, evento=ev,
            hash_sha256=_hash_evento(ev),
        )

    # Check 3: probe de leakage
    p_leakage = None
    if rodar_probe:
        kwargs = probe_kwargs or {}
        r = probar_evento(ev, **kwargs)
        p_leakage = r.p_outcome_mean
        if r.n_validas == 0:
            avisos.append(f"probe falhou: {r.erro}")
        elif r.is_leakage(LEAKAGE_THRESHOLD_DEFAULT):
            return ResultadoCuradoria(
                aprovado=False,
                razao=f"probe detectou leakage: p_outcome_mean={p_leakage:.3f} >= {LEAKAGE_THRESHOLD_DEFAULT}",
                evento=ev,
                hash_sha256=_hash_evento(ev),
                p_leakage=p_leakage,
                avisos=avisos,
            )

    # Aprovado: atualiza leakage_risk com base no probe
    if p_leakage is not None:
        ev = ev.model_copy(update={
            "leakage_risk": classificar_leakage(p_leakage),
            "audit_status": "aprovado_helena",
            "leakage_mitigations": ev.leakage_mitigations + [
                f"curador_oos_v1:probe_p={p_leakage:.3f}",
                f"cutoff_llm={CUTOFF_LLM.isoformat()}",
            ],
        })
    else:
        ev = ev.model_copy(update={
            "audit_status": "aprovado_helena",
            "leakage_mitigations": ev.leakage_mitigations + [
                "curador_oos_v1:probe_skipped",
                f"cutoff_llm={CUTOFF_LLM.isoformat()}",
            ],
        })

    return ResultadoCuradoria(
        aprovado=True,
        razao="todos os checks passaram",
        evento=ev,
        hash_sha256=_hash_evento(ev),
        p_leakage=p_leakage,
        avisos=avisos,
    )


def curar_lote(
    eventos: list[EventoPreditivoV1],
    rodar_probe: bool = True,
    probe_kwargs: Optional[dict] = None,
) -> dict:
    """Aplica curar_evento em lote. Retorna estatísticas + listas separadas."""
    aprovados: list[EventoPreditivoV1] = []
    vetados: list[dict] = []
    for ev in eventos:
        r = curar_evento(ev, rodar_probe=rodar_probe, probe_kwargs=probe_kwargs)
        if r.aprovado:
            aprovados.append(r.evento)
        else:
            vetados.append({
                "id": ev.id,
                "razao": r.razao,
                "p_leakage": r.p_leakage,
                "hash": r.hash_sha256,
            })
    return {
        "n_total": len(eventos),
        "n_aprovados": len(aprovados),
        "n_vetados": len(vetados),
        "taxa_aprovacao": len(aprovados) / len(eventos) if eventos else 0.0,
        "aprovados": aprovados,
        "vetados": vetados,
    }


def salvar_aprovados(
    aprovados: list[EventoPreditivoV1],
    path: str | Path,
) -> int:
    """Salva eventos aprovados em JSONL. Retorna n escritos."""
    return to_jsonl(aprovados, path)
