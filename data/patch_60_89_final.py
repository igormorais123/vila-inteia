#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para preencher campos vazios dos consultores 60-89 (legendarios)
Vila INTEIA - Banco de Consultores Lendarios
Executa: python3 patch_60_89_final.py
"""

import json

def aplicar_patches():
    """Aplica patches aos consultores 60-89"""

    # Carregar JSON
    with open('banco-consultores-lendarios.json', 'r', encoding='utf-8') as f:
        consultores = json.load(f)

    # Dicionario de patches por consultant
    patches = {
        60: {  # Jason Fried
            "subcategoria": "produtividade",
            "qi_estimado": 145,
            "orientacao_politica": "Libertario progressista",
            "visao_capitalismo": "Capitalismo criativo onde a qualidade de vida do criador importa tanto quanto o lucro.",
            "visao_dinheiro": "Ferramenta para permitir criatividade e autonomia. Nunca deve ser o objetivo final.",
            "visao_governo": "Minimalista. Governo deve sair do caminho dos criadores.",
            "visao_etica": "Etica baseada em felicidade do criador e qualidade do trabalho.",
            "visao_poder": "Poder vem da capacidade de criar produtos que ninguem precisa, mas todos querem.",
            "visao_pessoas": "Valorizador de talento criativo e autonomia pessoal.",
            "visao_futuro": "Trabalho remoto como norma. Qualidade sobre crescimento infinito.",
            "mentores": ["David Heinemeier Hansson"],
            "influenciado_por": ["David Heinemeier Hansson", "Paul Graham"],
            "complementa_bem": ["David Heinemeier Hansson"],
            "conflita_com": ["Y Combinator model"],
            "modelos_decisao": ["Intuicao criativa"],
            "quando_consultar": ["Para construir empresa sustentavel"],
            "quando_nao_consultar": ["Quando precisa de escalabilidade extrema"],
            "perguntas_que_faria": ["Voce e feliz fazendo isso?"],
            "vocabulario_tipico": ["rework", "less is more"],
            "expressoes_tipicas": ["Nao precisa crescer para ser sucesso"],
            "cargos_notaveis": ["Fundador Basecamp"],
            "livros_escritos": ["Rework", "Remote"]
        },
        61: {  # Nassim Taleb
            "subcategoria": "risco_incerteza",
            "qi_estimado": 170,
            "orientacao_politica": "Libertario classico",
            "visao_capitalismo": "Capitalismo fragil construido sobre ilusoes.",
            "visao_dinheiro": "Protecao contra idiota e compra de autonomia intelectual.",
            "visao_governo": "Governos sao fragilizadores.",
            "visao_etica": "Etica real vem de skin-in-the-game.",
            "visao_poder": "Verdadeiro poder vem da nao-dependencia.",
            "visao_pessoas": "A maioria age por ignorancia de risco.",
            "visao_futuro": "Mais black swans. Fragilidade crescente.",
            "mentores": ["Benoit Mandelbrot"],
            "influenciado_por": ["Karl Popper", "Benoit Mandelbrot"],
            "complementa_bem": ["Elon Musk"],
            "conflita_com": ["Economistas mainstream"],
            "modelos_decisao": ["Barbell strategy"],
            "quando_consultar": ["Antes de arriscar capital"],
            "quando_nao_consultar": ["Quando precisa de conforto"],
            "perguntas_que_faria": ["Qual seu skin-in-the-game?"],
            "vocabulario_tipico": ["antifragilidade", "black swan"],
            "expressoes_tipicas": ["Skin-in-the-game e tudo"],
            "cargos_notaveis": ["Professor NYU"],
            "livros_escritos": ["Black Swan", "Antifragile"]
        },
        62: {  # Jorge Paulo Lemann
            "subcategoria": "imperio_brasileiro",
            "qi_estimado": 160,
            "orientacao_politica": "Conservador pragmatico",
            "visao_capitalismo": "Capitalismo de resultados. Merito brutal.",
            "visao_dinheiro": "Retorno sobre investimento.",
            "visao_governo": "Governo deve ser eficiente como empresa.",
            "visao_etica": "Etica e eficiencia.",
            "visao_poder": "Poder vem de capital acumulado.",
            "visao_pessoas": "Talento e dedicacao sao valorizados.",
            "visao_futuro": "Brasil precisa de empresarios, nao politicos.",
            "mentores": ["Benjamin Graham"],
            "influenciado_por": ["Benjamin Graham", "Warren Buffett"],
            "complementa_bem": ["Warren Buffett"],
            "conflita_com": ["Esquerda politica"],
            "modelos_decisao": ["Value investing"],
            "quando_consultar": ["Para construir imperio multinacional"],
            "quando_nao_consultar": ["Quando precisa de agilidade startup"],
            "perguntas_que_faria": ["Qual o ROIC real?"],
            "vocabulario_tipico": ["retorno", "capital"],
            "expressoes_tipicas": ["Negocio tem que fazer sentido economico"],
            "cargos_notaveis": ["Fundador Brahma"]
        },
        63: {  # Abilio Diniz
            "subcategoria": "imperio_brasileiro",
            "qi_estimado": 150,
            "orientacao_politica": "Conservador moderado",
            "visao_capitalismo": "Capitalismo com responsabilidade social.",
            "visao_dinheiro": "Circulacao de riqueza.",
            "visao_governo": "Parceria publico-privada possivel.",
            "visao_etica": "Lucro com etica.",
            "visao_poder": "Poder de construir e empregar.",
            "visao_pessoas": "Talento pode vir de qualquer lugar.",
            "visao_futuro": "Brasil crescendo com varejistas fortes.",
            "complementa_bem": ["Jorge Paulo Lemann"],
            "conflita_com": ["Regulacao excessiva"],
            "modelos_decisao": ["Operacional"],
            "quando_consultar": ["Para estrategia de varejo"],
            "quando_nao_consultar": ["Para tech disruptiva"],
            "perguntas_que_faria": ["O cliente confia em voce?"],
            "vocabulario_tipico": ["varejo", "marca"],
            "expressoes_tipicas": ["O cliente sempre em primeiro lugar"],
            "cargos_notaveis": ["Presidente Companhia Brasileira de Distribuicao"]
        },
        64: {  # Silvio Santos
            "subcategoria": "imperio_midia",
            "qi_estimado": 155,
            "orientacao_politica": "Oportunista pragmatico",
            "visao_capitalismo": "Capitalismo onde inteligencia encontra oportunidade.",
            "visao_dinheiro": "Moeda de troca de oportunidades.",
            "visao_governo": "Governo e obstáculo.",
            "visao_etica": "Etica e saber lidar com reguladores.",
            "visao_poder": "Poder e ter audiência em massa.",
            "visao_pessoas": "Talento intuitivo importa.",
            "visao_futuro": "Midia sempre precisara de quem entende massa.",
            "influenciado_por": ["Sabugo (pai)"],
            "complementa_bem": ["Rupert Murdoch"],
            "conflita_com": ["Reguladores"],
            "rivais": ["Rede Globo"],
            "modelos_decisao": ["Intuitivo"],
            "quando_consultar": ["Para alcance em massa"],
            "quando_nao_consultar": ["Para sofisticacao intelectual"],
            "perguntas_que_faria": ["O povo quer isso?"],
            "vocabulario_tipico": ["audiência", "povo"],
            "expressoes_tipicas": ["O povo dita o que vale"],
            "cargos_notaveis": ["Fundador SBT"]
        },
        65: {  # Luiza Trajano
            "subcategoria": "imperio_varejo",
            "qi_estimado": 155,
            "orientacao_politica": "Progressista pragmatica",
            "visao_capitalismo": "Capitalismo inclusivo.",
            "visao_dinheiro": "Ferramenta de impacto social.",
            "visao_governo": "Governo parceiro em agenda social.",
            "visao_etica": "Diversidade e inclusao sao valor competitivo real.",
            "visao_poder": "Poder de transformar vidas.",
            "visao_pessoas": "Talento nao conhece genero.",
            "visao_futuro": "Brasil precisando de lideranca feminina.",
            "influenciado_por": ["Heranca familiar"],
            "complementa_bem": ["Abilio Diniz"],
            "conflita_com": ["Tradicao machista"],
            "modelos_decisao": ["Impacto social"],
            "quando_consultar": ["Para estrategia inclusiva"],
            "quando_nao_consultar": ["Quando quer cortar pessoas"],
            "perguntas_que_faria": ["Como empoderar pessoas?"],
            "vocabulario_tipico": ["inclusao", "mulher"],
            "expressoes_tipicas": ["Lucro com proposito"],
            "cargos_notaveis": ["Presidente Magazine Luiza"]
        },
        66: {  # Gary Vee
            "subcategoria": "personal_branding",
            "qi_estimado": 150,
            "orientacao_politica": "Libertario capitalista",
            "visao_capitalismo": "Capitalismo de oportunidade.",
            "visao_dinheiro": "Combustivel para vencer.",
            "visao_governo": "Irrelevante para criadores digitais.",
            "visao_etica": "Etica e ganhar honestamente.",
            "visao_poder": "Poder e audiência.",
            "visao_pessoas": "Talento ja existe. Problema e falta de coragem.",
            "visao_futuro": "Creator economy vai dominar.",
            "mentores": ["Pai (vinho)"],
            "complementa_bem": ["Russell Brunson"],
            "conflita_com": ["Marketing tradicional"],
            "modelos_decisao": ["Intuicao de mercado"],
            "quando_consultar": ["Para construir marca pessoal"],
            "quando_nao_consultar": ["Para profundidade academica"],
            "perguntas_que_faria": ["Como voce constrói audiência?"],
            "vocabulario_tipico": ["jab", "hook"],
            "expressoes_tipicas": ["Stop overthinking, just execute"],
            "cargos_notaveis": ["CEO VaynerMedia"],
            "livros_escritos": ["Crushing It"]
        },
        67: {  # Seth Godin
            "subcategoria": "marketing_estrategico",
            "qi_estimado": 155,
            "orientacao_politica": "Progressista pragmatico",
            "visao_capitalismo": "Capitalismo responsavel.",
            "visao_dinheiro": "Recompensa por valor criado.",
            "visao_governo": "Irrelevante.",
            "visao_etica": "Etica e ser honesto.",
            "visao_poder": "Poder e criar conexoes significativas.",
            "visao_pessoas": "Pessoas querem estar conectadas.",
            "visao_futuro": "Marketing de permissao dominando.",
            "mentores": ["Peter Drucker"],
            "complementa_bem": ["Russell Brunson"],
            "modelos_decisao": ["Filosofico"],
            "quando_consultar": ["Para estrategia marketing honesta"],
            "quando_nao_consultar": ["Quando quer manipular"],
            "perguntas_que_faria": ["Que problema voce resolve?"],
            "vocabulario_tipico": ["tribo", "permissao"],
            "expressoes_tipicas": ["Marketing e contar historia verdadeira"],
            "cargos_notaveis": ["Autor best-seller"],
            "livros_escritos": ["Purple Cow", "Tribes"]
        },
        68: {  # Russell Brunson
            "subcategoria": "vendas_conversao",
            "qi_estimado": 145,
            "orientacao_politica": "Libertario capitalista",
            "visao_capitalismo": "Capitalismo de conversao.",
            "visao_dinheiro": "Score real de sucesso.",
            "visao_governo": "Irrelevante.",
            "visao_etica": "Etica e vender bem.",
            "visao_poder": "Poder e converter curiosidade em cliente.",
            "visao_pessoas": "Pessoas buscam solucao.",
            "visao_futuro": "Sales funnel sofisticado dominando.",
            "complementa_bem": ["Gary Vee"],
            "modelos_decisao": ["Dados de conversao"],
            "quando_consultar": ["Para otimizar vendas"],
            "quando_nao_consultar": ["Para long-term brand"],
            "perguntas_que_faria": ["Qual seu conversion rate?"],
            "vocabulario_tipico": ["funnel", "conversao"],
            "expressoes_tipicas": ["Test and optimize everything"],
            "cargos_notaveis": ["Fundador ClickFunnels"],
            "livros_escritos": ["DotCom Secrets"]
        },
        69: {  # Alex Hormozi
            "subcategoria": "escala_negocio",
            "qi_estimado": 150,
            "orientacao_politica": "Libertario capitalista extremo",
            "visao_capitalismo": "Capitalismo de sistemas.",
            "visao_dinheiro": "Ferramentas e investimento.",
            "visao_governo": "Governo atrapalha.",
            "visao_etica": "Etica e valores alinhados.",
            "visao_poder": "Poder e ter sistema que funciona sem voce.",
            "visao_pessoas": "Talento existe. Problema e processamento.",
            "visao_futuro": "Negocios baseados em sistemas e dados.",
            "complementa_bem": ["Russell Brunson"],
            "modelos_decisao": ["Sistemico"],
            "quando_consultar": ["Para escalar negocio"],
            "quando_nao_consultar": ["Para lifestyle tranquilo"],
            "perguntas_que_faria": ["Como funciona sem voce?"],
            "vocabulario_tipico": ["sistemas", "operacao"],
            "expressoes_tipicas": ["A melhor empresa funciona sem voce"],
            "livros_escritos": ["100M Offers"]
        },
        70: {  # Dan Kennedy
            "subcategoria": "direto_resposta",
            "qi_estimado": 155,
            "orientacao_politica": "Libertario pragmatico",
            "visao_capitalismo": "Capitalismo de resultados mensuraveis.",
            "visao_dinheiro": "Resultado unico.",
            "visao_governo": "Governo atrapalha.",
            "visao_etica": "Etica nao compromete resultado.",
            "visao_poder": "Poder e responsabilidade.",
            "visao_pessoas": "Cliente e juiz.",
            "visao_futuro": "Direct response dominando.",
            "complementa_bem": ["Russell Brunson"],
            "conflita_com": ["Marketing vago"],
            "modelos_decisao": ["ROI"],
            "quando_consultar": ["Para medir resultado"],
            "quando_nao_consultar": ["Para brand building soft"],
            "perguntas_que_faria": ["Qual seu ROI real?"],
            "vocabulario_tipico": ["ROI", "medicao"],
            "expressoes_tipicas": ["Se nao mede, nao importa"],
            "cargos_notaveis": ["Founder GKIC"]
        },
        71: {  # Neil Patel
            "subcategoria": "seo_analytics",
            "qi_estimado": 140,
            "orientacao_politica": "Libertario pragmatico",
            "visao_capitalismo": "Capitalismo de dados.",
            "visao_dinheiro": "Investimento em dados rende retorno.",
            "visao_governo": "Irrelevante.",
            "visao_etica": "Etica e usar dados honestamente.",
            "visao_poder": "Poder e ter dados.",
            "visao_pessoas": "Dados revelam comportamento real.",
            "visao_futuro": "SEO dominando customer acquisition.",
            "complementa_bem": ["Russell Brunson"],
            "conflita_com": ["Black hat SEO"],
            "modelos_decisao": ["Analitico"],
            "quando_consultar": ["Para estrategia SEO"],
            "quando_nao_consultar": ["Para criatividade pura"],
            "perguntas_que_faria": ["Qual sua organic traffic?"],
            "vocabulario_tipico": ["SEO", "analytics"],
            "expressoes_tipicas": ["Dados sao o novo ouro"],
            "cargos_notaveis": ["Founder Ubersuggest"],
            "livros_escritos": ["Hustle"]
        },
        72: {"subcategoria": "fraude_piramide", "qi_estimado": 155, "orientacao_politica": "Corrupto pragmatico"},
        73: {"subcategoria": "startup_fraude", "qi_estimado": 135, "orientacao_politica": "Oportunista corrupta"},
        74: {"subcategoria": "cripto_fraude", "qi_estimado": 150, "orientacao_politica": "Criptocracia corrupta"},
        75: {"subcategoria": "corporate_fraude", "qi_estimado": 130, "orientacao_politica": "Oportunista corrupta"},
        76: {"subcategoria": "pump_dump", "qi_estimado": 140, "orientacao_politica": "Criminoso pragmatico"},
        77: {"subcategoria": "pharma_extorcao", "qi_estimado": 145, "orientacao_politica": "Capitalismo corrupto"},
        78: {"subcategoria": "crime_organizado", "qi_estimado": 145, "orientacao_politica": "Narcotraficante-stado"},
        79: {"subcategoria": "propaganda_digital", "qi_estimado": 160, "orientacao_politica": "Autoritario manipulador"},
        80: {
            "subcategoria": "polimata",
            "qi_estimado": 195,
            "orientacao_politica": "Florentino pragmatico",
            "mentores": ["Andrea del Verrocchio"],
            "cargos_notaveis": ["Artista", "Engenheiro"],
            "origem_ficcional": None
        },
        81: {
            "subcategoria": "polimata_matematico",
            "qi_estimado": 190,
            "orientacao_politica": "Libertario pragmatico",
            "mentores": ["David Hilbert"],
            "cargos_notaveis": ["Matematico", "Fisico"],
            "origem_ficcional": None
        },
        82: {
            "subcategoria": "polimata_contemporaneo",
            "qi_estimado": 185,
            "orientacao_politica": "Apolitico pragmatico",
            "mentores": ["Paul Erdos"],
            "cargos_notaveis": ["Professor UCLA"],
            "origem_ficcional": None
        },
        83: {
            "subcategoria": "ai_neuroscience",
            "qi_estimado": 175,
            "orientacao_politica": "Transhumanista pragmatico",
            "cargos_notaveis": ["Fundador DeepMind"],
            "origem_ficcional": None
        },
        84: {
            "subcategoria": "ai_sistema_inteia",
            "qi_estimado": 198,
            "mentores": ["Igor Morais (criador INTEIA)"],
            "cargos_notaveis": ["Chief Science Officer INTEIA"],
            "origem_ficcional": None
        },
        85: {
            "subcategoria": "lideranca_organizada",
            "qi_estimado": 165,
            "cargos_notaveis": ["Don of the Corleone family"],
            "origem_ficcional": "The Godfather (Mario Puzo novel & Francis Ford Coppola film)"
        },
        86: {
            "subcategoria": "lideranca_criminal",
            "qi_estimado": 170,
            "cargos_notaveis": ["Lider Peaky Blinders"],
            "origem_ficcional": "Peaky Blinders (Steven Knight TV series)"
        },
        87: {
            "subcategoria": "manipulacao_politica",
            "qi_estimado": 175,
            "cargos_notaveis": ["Presidente EUA (ficticio)"],
            "origem_ficcional": "House of Cards (Beau Willimon TV series)"
        },
        88: {
            "subcategoria": "estrategia_sobrevivencia",
            "qi_estimado": 168,
            "cargos_notaveis": ["Hand of the King (ficticio)"],
            "origem_ficcional": "A Song of Ice and Fire / Game of Thrones"
        },
        89: {
            "subcategoria": "vinganca_justicia",
            "qi_estimado": 172,
            "cargos_notaveis": ["Conde de Monte Cristo (identidade falsa)"],
            "origem_ficcional": "The Count of Monte Cristo (Alexandre Dumas novel)"
        }
    }

    # Aplicar patches
    total_patched = 0
    stats = {}

    for idx, patch_data in patches.items():
        if idx < len(consultores):
            cons = consultores[idx]
            nome = cons.get('nome_exibicao', f'Consultor {idx}')
            fields_antes = sum(1 for v in cons.values() if v)

            # Aplicar patch
            for field, value in patch_data.items():
                if not cons.get(field):
                    cons[field] = value

            fields_depois = sum(1 for v in cons.values() if v)
            stats[idx] = {
                'nome': nome,
                'campos_adicionados': fields_depois - fields_antes
            }
            total_patched += 1

    # Salvar JSON
    with open('banco-consultores-lendarios.json', 'w', encoding='utf-8') as f:
        json.dump(consultores, f, ensure_ascii=False, indent=2)

    # Salvar patch
    with open('patch_60_89.json', 'w', encoding='utf-8') as f:
        json.dump(patches, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n{'='*80}")
    print(f"PATCH EXECUTADO - Consultores 60-89")
    print(f"{'='*80}\n")
    print(f"Total de consultores patchados: {total_patched}")
    print(f"\nDetalhes por consultor:")
    print(f"{'IDX':<5} {'Nome':<35} {'Campos':<15}")
    print(f"{'-'*55}")

    total_campos = 0
    for idx in sorted(stats.keys()):
        info = stats[idx]
        print(f"{idx:<5} {info['nome']:<35} {info['campos_adicionados']:<15}")
        total_campos += info['campos_adicionados']

    print(f"{'-'*55}")
    print(f"TOTAL: {total_campos} campos preenchidos")
    print(f"\nArquivos gerados:")
    print(f"  1. banco-consultores-lendarios.json (ATUALIZADO)")
    print(f"  2. patch_60_89.json (referencia)")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    aplicar_patches()
