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

"""Dados dos 144 Consultores Lendarios para seed do banco de dados.

Blocos:
- 001-025: Visionarios, Estrategia, Investidores, Negociacao, Tech
- 026-050: Marca, Politica Internacional, Politica Brasileira
- 051-075: Resiliencia, Lado Negro, MKT Digital
- 076-100: QI Extremo, IA/Futuro, Ficticios, Omega
- 101-110: JURISTAS LENDARIOS BRASILEIROS (Rui Barbosa, Miguel Reale, etc.)
- 111-120: LIDERES MORAIS E MONARCAS (Elizabeth II, Joao Paulo II)
- 121-130: FILOSOFOS (Socrates, Nietzsche, Marco Aurelio, Seneca, Epicteto)
- 131-140: PSICOLOGOS (Jung, Viktor Frankl, Temple Grandin, Freud, Kahneman)
- 141-142: MKT DIGITAL & CURSOS (Hormozi, Brunson) — do bloco 141-156 apenas CL141-CL142 ativos no JSON
- 143-144: HIPNOSE TERAPEUTICA & DESIGN SCIENCE (Milton Erickson, Prof. Edu)

NOTA: O bloco_141_156_mkt_digital_cursos.py contem CL141-CL156 (16 consultores planejados),
mas apenas CL141-CL142 foram adicionados ao JSON principal. Os IDs CL143-CL156 desse bloco
conflitam com CL143-CL144 (Erickson/Edu) que sao a fonte de verdade no JSON. Os consultores
CL143-CL156 do bloco de MKT Digital precisarao ser renumerados em trabalho futuro.
"""
