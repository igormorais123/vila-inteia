# -*- coding: utf-8 -*-
# ============================================================================
# Copyright (c) 2024-2026 INTEIA - Inteligencia Estrategica
# Todos os direitos reservados.
#
# Este software e propriedade confidencial da INTEIA.
# A reproducao, distribuicao ou uso nao autorizado deste material
# e estritamente proibido sem consentimento previo por escrito.
#
# Autor: INTEIA
# Contato: igor@inteia.com.br
# Site: https://inteia.com.br
# ============================================================================

"""
Gerador de perfis completos a partir de templates compactos.
Preenche campos derivados automaticamente a partir dos dados-chave.
"""


def gerar_instrucao(nome, titulo, personalidade, areas, tom):
    """Gera instrucao_comportamental a partir de dados-chave."""
    areas_str = ", ".join(areas[:5])
    return (
        f"Voce e {nome}, {titulo}. "
        f"{personalidade} "
        f"Suas areas de expertise sao: {areas_str}. "
        f"Responda sempre no tom {tom}. "
        f"Mantenha coerencia com sua personalidade e valores documentados."
    )


def gerar_instrucao_lado_negro(nome, titulo, crime, red_flags):
    """Gera instrucao para consultores do lado negro (analise, nao glorificacao)."""
    flags = ", ".join(red_flags[:4])
    return (
        f"Voce analisa como {nome} ({titulo}) pensaria e agiria. "
        f"Crime/falha: {crime}. "
        f"Seu papel e REVELAR red flags e padroes de manipulacao: {flags}. "
        f"NAO glorifique. Ensine a reconhecer e evitar esses padroes."
    )


def expandir_perfil(p):
    """Expande um perfil compacto em registro completo de ~100 campos."""
    cat = p.get("categoria", "estrategia")
    eh_negro = cat == "lado_negro"

    # Instrucao comportamental
    if "instrucao_comportamental" not in p:
        if eh_negro:
            p["instrucao_comportamental"] = gerar_instrucao_lado_negro(
                p["nome_exibicao"],
                p.get("titulo", ""),
                p.get("maior_fracasso", ""),
                p.get("tracos_sombra", []),
            )
        else:
            p["instrucao_comportamental"] = gerar_instrucao(
                p["nome_exibicao"],
                p.get("titulo", ""),
                p.get("personalidade_resumo", ""),
                p.get("areas_expertise", []),
                p.get("tom_voz", "direto e assertivo"),
            )

    # Defaults para campos opcionais
    defaults = {
        "subtitulo": p.get("titulo", ""),
        "subcategoria": None,
        "tier": "A",
        "imperio_principal": None,
        "patrimonio_estimado": None,
        "setor_principal": None,
        "origem_ficcional": None,
        "qi_estimado": None,
        "historia_origem": None,
        "momento_definidor": None,
        "maior_conquista": None,
        "maior_fracasso": None,
        "legado": None,
        "empresas": [],
        "cargos_notaveis": [],
        "livros_escritos": [],
        "conceitos_criados": [],
        "estilo_comunicacao": p.get("tom_voz", "Direto e assertivo"),
        "tom_voz": "direto, confiante",
        "nivel_agressividade": 5,
        "nivel_empatia": 5,
        "nivel_humor": 5,
        "nivel_formalidade": 6,
        "nivel_carisma": 7,
        "nivel_extroversao": 6,
        "tracos_dominantes": [],
        "tracos_sombra": [],
        "valores_fundamentais": [],
        "medos_vulnerabilidades": [],
        "vieses_conhecidos": [],
        "areas_expertise": [],
        "frameworks_mentais": [],
        "principios_fundamentais": [],
        "modelos_decisao": [],
        "estilo_pensamento": "pragmatico",
        "horizonte_temporal": "longo",
        "tolerancia_risco": 6,
        "velocidade_decisao": 6,
        "preferencia_dados_intuicao": "equilibrado",
        "capacidade_abstrata": 7,
        "idiomas": ["ingles"],
        "estilo_argumentacao": "logico",
        "uso_metaforas": 5,
        "capacidade_persuasao": 7,
        "presenca_publica": 7,
        "estilo_escrita": "Conciso e direto",
        "vocabulario_tipico": [],
        "expressoes_tipicas": [],
        "frases_celebres": [],
        "frase_chave": None,
        "estilo_lideranca": "estrategico",
        "capacidade_delegacao": 6,
        "como_trata_subordinados": "Exigente mas justo",
        "como_trata_superiores": "Respeitoso mas firme",
        "como_trata_iguais": "Competitivo mas colaborativo",
        "abordagem_problemas": "Analisa dados, define estrategia, executa",
        "reacao_sob_pressao": "Mantem a calma e foca na solucao",
        "como_lida_fracasso": "Aprende e segue em frente",
        "como_lida_sucesso": "Celebra brevemente e busca o proximo desafio",
        "estilo_decisao_primario": "analitico",
        "orientacao_politica": None,
        "visao_governo": None,
        "visao_capitalismo": None,
        "visao_etica": None,
        "visao_poder": None,
        "visao_dinheiro": None,
        "visao_pessoas": None,
        "visao_futuro": None,
        "consultor_para": [],
        "quando_consultar": [],
        "quando_nao_consultar": [],
        "perguntas_que_faria": [],
        "abordagem_consultoria": "Direto ao ponto com foco em resultados",
        "estilo_feedback": "Direto e construtivo",
        "nivel_confiabilidade": 8,
        "complementa_bem": [],
        "conflita_com": [],
        "mentores": [],
        "rivais": [],
        "influenciou": [],
        "influenciado_por": [],
        "rede_principal": [],
        "material_referencia": [],
        "tags": [],
        "foto_url": None,
        "ativo": True,
    }

    # Mesclar defaults com dados fornecidos (dados fornecidos tem prioridade)
    resultado = {}
    for key, default_val in defaults.items():
        resultado[key] = p.get(key, default_val)

    # Campos obrigatorios (sempre do perfil)
    for key in [
        "id",
        "numero_lista",
        "nome",
        "nome_exibicao",
        "titulo",
        "status_vida",
        "ano_nascimento",
        "ano_morte",
        "nacionalidade",
        "categoria",
        "biografia_resumida",
        "arquetipo",
        "personalidade_resumo",
        "instrucao_comportamental",
    ]:
        resultado[key] = p[key]

    return resultado
