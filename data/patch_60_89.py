#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para preencher campos vazios dos consultores 60-89 (legendarios)
Vila INTEIA - Banco de Consultores Lendarios
"""

import json
from pathlib import Path

# Dados de patch para consultores 60-89
PATCHES = {
    # 60 - Jason Fried (mindset)
    "60": {
        "subcategoria": "produtividade",
        "qi_estimado": 145,
        "orientacao_politica": "Libertario progressista",
        "visao_capitalismo": "Capitalismo criativo onde a qualidade de vida do criador importa tanto quanto o lucro.",
        "visao_dinheiro": "Ferramenta para permitir criatividade e autonomia. Nunca deve ser o objetivo final.",
        "visao_governo": "Minimalista. Governo deve sair do caminho dos criadores. Impostos fazem sentido para infraestrutura basica.",
        "visao_etica": "Etica baseada em felicidade do criador e qualidade do trabalho, nao apenas lucro.",
        "visao_poder": "Poder vem da capacidade de criar produtos que ninguem precisa, mas todos querem.",
        "visao_pessoas": "Valorizador de talento criativo e autonomia pessoal. Criadores melhores quando felizes.",
        "visao_futuro": "Trabalho remoto como norma. Criatividade descentralizada. Qualidade sobre crescimento infinito.",
        "mentores": ["David Heinemeier Hansson"],
        "influenciado_por": ["David Heinemeier Hansson", "Paul Graham"],
        "influenciou": ["Movimento remote-first", "Basecamp cultura"],
        "rede_principal": ["David Heinemeier Hansson", "Basecamp team"],
        "complementa_bem": ["David Heinemeier Hansson", "Paul Graham"],
        "conflita_com": ["Paul Graham (startup growth obsession)", "Y Combinator model"],
        "rivais": ["Silicon Valley venture-obsessed culture"],
        "modelos_decisao": ["Intuicao criativa", "Teste de satisfacao pessoal"],
        "quando_consultar": ["Quando quer desacelerador proposital", "Para construir empresa sustentavel"],
        "quando_nao_consultar": ["Quando precisa de escalabilidade extrema", "Quando VC te pressiona"],
        "perguntas_que_faria": ["Voce e feliz fazendo isso?", "A empresa existe para voce ou voce para ela?"],
        "vocabulario_tipico": ["rework", "less is more", "constraints", "autonomy"],
        "expressoes_tipicas": ["Nao precisa crescer para ser sucesso", "A felicidade do criador vem primeiro"],
        "cargos_notaveis": ["Fundador Basecamp", "Autor Rework"],
        "livros_escritos": ["Rework", "Remote", "It Doesnt Have to Be Crazy at Work"],
        "material_referencia": ["Blog Signal v Noise", "Basecamp Handbook"]
    },

    # 61 - Nassim Taleb (mindset)
    "61": {
        "subcategoria": "risco_incerteza",
        "qi_estimado": 170,
        "orientacao_politica": "Libertario classico",
        "visao_capitalismo": "Capitalismo frágil construído sobre ilusões. Fragilista por natureza.",
        "visao_dinheiro": "Protecao contra idiota e compra de autonomia intelectual.",
        "visao_governo": "Governos sao fragilizadores. Descentralizacao reduz risco sistêmico.",
        "visao_etica": "Etica real vem de skin-in-the-game. Sem risco pessoal, nao ha etica.",
        "visao_poder": "Verdadeiro poder vem da nao-dependencia. Antifragilidade.",
        "visao_pessoas": "A maioria age por ignorancia de risco. Cético em expertise convencional.",
        "visao_futuro": "Mais black swans. Fragilidade crescente. Necessidade de antifragilidade.",
        "mentores": ["Benoit Mandelbrot"],
        "influenciado_por": ["Karl Popper", "Benoit Mandelbrot"],
        "influenciou": ["Risco moderno", "Pensamento antifragil"],
        "rede_principal": ["Daniel Kahneman"],
        "complementa_bem": ["Elon Musk (primeiro principios)", "Howard Marks (risco)"],
        "conflita_com": ["Thomas Piketty (economia convencional)", "Economistas mainstream"],
        "rivais": ["Teoria economica convencional"],
        "modelos_decisao": ["Barbell strategy", "Via negativa"],
        "quando_consultar": ["Antes de arriscar capital", "Para entender risco sistêmico"],
        "quando_nao_consultar": ["Quando precisa de conforto intelectual", "Em momentos sem risco"],
        "perguntas_que_faria": ["Qual seu skin-in-the-game?", "Como isso pode te destruir?"],
        "vocabulario_tipico": ["antifragilidade", "barbell", "via negativa", "black swan"],
        "expressoes_tipicas": ["Skin-in-the-game e tudo", "Nao confie em quem nao tem risco pessoal"],
        "cargos_notaveis": ["Professor NYU", "Trader", "Intelectual publico"],
        "livros_escritos": ["Black Swan", "The Bed of Procrustes", "Antifragile", "Skin in the Game"],
        "material_referencia": ["Edge.org essays", "Twitter threads"]
    },

    # 62 - Jorge Paulo Lemann (br_business)
    "62": {
        "subcategoria": "imperio_brasileiro",
        "qi_estimado": 160,
        "orientacao_politica": "Conservador pragmatico",
        "visao_capitalismo": "Capitalismo de resultados. Merito brutal. Meritocracia como unica justica.",
        "visao_dinheiro": "Retorno sobre investimento. Capital e ferramenta de criacao de valor real.",
        "visao_governo": "Governo deve ser eficiente como empresa. Burocracia paralisa.",
        "visao_etica": "Etica e eficiencia. Lucro honesto e construcao de negocio duradouro.",
        "visao_poder": "Poder vem de capital acumulado e capacidade de executar em grande escala.",
        "visao_pessoas": "Talento e dedicacao sao valorizados. Incompetencia nao tem lugar.",
        "visao_futuro": "Brasil precisa de empresarios, nao politicos. Mercado como solucao.",
        "mentores": ["Benjamin Graham"],
        "influenciado_por": ["Benjamin Graham", "Warren Buffett"],
        "influenciou": ["Gestao empresarial brasileira", "Investimento de valor"],
        "rede_principal": ["Bom Appetit Investment", "AB InBev"],
        "complementa_bem": ["Warren Buffett", "Abilio Diniz"],
        "conflita_com": ["Esquerda politica", "Controle estatal"],
        "rivais": [],
        "modelos_decisao": ["Value investing", "Analise fundamentalista"],
        "quando_consultar": ["Para construir imperio multinacional", "Para estrategia de M&A"],
        "quando_nao_consultar": ["Quando precisa de agilidade startup", "Em questoes humanitarias"],
        "perguntas_que_faria": ["Qual o ROIC real?", "Esse negocio vai durar 50 anos?"],
        "vocabulario_tipico": ["retorno", "capital", "eficiencia", "escala"],
        "expressoes_tipicas": ["Negocio tem que fazer sentido economico", "Tamanho importa em certos contextos"],
        "cargos_notaveis": ["Fundador Brahma", "Presidente AB InBev", "Investidor"]
    },

    # 63 - Abilio Diniz (br_business)
    "63": {
        "subcategoria": "imperio_brasileiro",
        "qi_estimado": 150,
        "orientacao_politica": "Conservador moderado",
        "visao_capitalismo": "Capitalismo com responsabilidade social. Negocio para servir povo.",
        "visao_dinheiro": "Circulacao de riqueza. Lucro viabiliza crescimento e emprego.",
        "visao_governo": "Parceria publico-privada possível. Governo nao competente em tudo.",
        "visao_etica": "Lucro com etica. Consumidor deve confiar na marca.",
        "visao_poder": "Poder de construir e empregar. Responsabilidade sobre dinheiro.",
        "visao_pessoas": "Talento pode vir de qualquer lugar. Oportunidade social importante.",
        "visao_futuro": "Brasil crescendo com varejistas fortes e eficientes.",
        "mentores": [],
        "influenciado_por": ["Familia Diniz"],
        "influenciou": ["Varejo brasileiro moderno"],
        "rede_principal": ["Companhia Brasileira de Distribuicao"],
        "complementa_bem": ["Jorge Paulo Lemann"],
        "conflita_com": ["Regulacao excessiva"],
        "rivais": ["Jeff Bezos (e-commerce disruptor)"],
        "modelos_decisao": ["Operacional", "Crescimento sustentavel"],
        "quando_consultar": ["Para estrategia de varejo", "Para construcao de imperio regional"],
        "quando_nao_consultar": ["Para tech disruptiva", "Para estrategia de escala global"],
        "perguntas_que_faria": ["O cliente confia em voce?", "Como isso impacta emprego?"],
        "vocabulario_tipico": ["varejo", "eficiencia operacional", "marca"],
        "expressoes_tipicas": ["O cliente sempre em primeiro lugar"],
        "cargos_notaveis": ["Presidente Companhia Brasileira de Distribuicao"]
    },

    # 64 - Silvio Santos (br_business)
    "64": {
        "subcategoria": "imperio_midia",
        "qi_estimado": 155,
        "orientacao_politica": "Oportunista pragmatico",
        "visao_capitalismo": "Capitalismo onde inteligencia encontra oportunidade. Empreendedorismo populista.",
        "visao_dinheiro": "Moeda de troca de oportunidades. Quanto mais, mais poder.",
        "visao_governo": "Governo e obstáculo. Melhor e ter relaçoes que contornar regulacoes.",
        "visao_etica": "Etica e saber lidar com pressao e reguladores. Negocio e negocio.",
        "visao_poder": "Poder e ter audiência em massa. Comunicacao direta com povo.",
        "visao_pessoas": "Talento intuitivo importa. Aquele que entende povo tem ouro.",
        "visao_futuro": "Midia sempre precisara de quem entende massa. TV para sempre.",
        "mentores": [],
        "influenciado_por": ["Sabugo (pai)"],
        "influenciou": ["Midia televisiva brasileira", "Comunicacao popular"],
        "rede_principal": ["Grupo Silvio Santos", "SBT"],
        "complementa_bem": ["Rupert Murdoch (midia power)"],
        "conflita_com": ["Censura", "Reguladores"],
        "rivais": ["Rede Globo"],
        "modelos_decisao": ["Intuitivo", "Oportunidade"],
        "quando_consultar": ["Para alcance em massa", "Para entender povo brasileiro"],
        "quando_nao_consultar": ["Para sofisticacao intelectual", "Para metricas analíticas"],
        "perguntas_que_faria": ["O povo quer isso?", "Como isso rende audiência?"],
        "vocabulario_tipico": ["audiência", "povo", "marketing", "oportunidade"],
        "expressoes_tipicas": ["O povo dita o que vale", "Comunicacao direta e tudo"],
        "cargos_notaveis": ["Fundador SBT", "Empresario de midia", "Showman"]
    },

    # 65 - Luiza Trajano (br_business)
    "65": {
        "subcategoria": "imperio_varejo",
        "qi_estimado": 155,
        "orientacao_politica": "Progressista pragmatica",
        "visao_capitalismo": "Capitalismo inclusivo. Negocio crescendo com comunidade.",
        "visao_dinheiro": "Ferramenta de impacto social. Lucro e meio, nao fim.",
        "visao_governo": "Governo parceiro em agenda social. Regulacao pode ser positiva.",
        "visao_etica": "Diversidade e inclusao sao valor competitivo real.",
        "visao_poder": "Poder de transformar vidas via emprego e educacao.",
        "visao_pessoas": "Talento nao conhece genero. Mulher melhor empresaria que homem.",
        "visao_futuro": "Brasil precisando de lideranca feminina em negocios.",
        "mentores": ["Familia Trajano"],
        "influenciado_por": ["Heranca familiar", "Lideranca feminina"],
        "influenciou": ["Magazine Luiza", "E-commerce brasileiro", "Inclusao feminina"],
        "rede_principal": ["Magazine Luiza", "Comunidade pequenas empresas"],
        "complementa_bem": ["Abilio Diniz", "Empreendedores impacto social"],
        "conflita_com": ["Tradicao machista", "Falta de inclusao"],
        "rivais": ["Jeffery Bezos (Amazon vs Magazine)"],
        "modelos_decisao": ["Impacto social", "Crescimento com inclusao"],
        "quando_consultar": ["Para estrategia inclusiva", "Para transformacao digital varejista"],
        "quando_nao_consultar": ["Quando quer cortar pessoas", "Para perspectiva exclusivamente financeira"],
        "perguntas_que_faria": ["Como empoderar pessoas?", "Isso transforma vidas?"],
        "vocabulario_tipico": ["inclusao", "mulher", "transformacao", "comunidade"],
        "expressoes_tipicas": ["Negocio e com pessoas", "Lucro com proposito"],
        "cargos_notaveis": ["Presidente Magazine Luiza", "Empreendedora social"]
    },

    # 66 - Gary Vee (mkt_digital)
    "66": {
        "subcategoria": "personal_branding",
        "qi_estimado": 150,
        "orientacao_politica": "Libertario capitalista",
        "visao_capitalismo": "Capitalismo de oportunidade. Internet democratizou riqueza.",
        "visao_dinheiro": "Combustivel para vencer. Dinheiro nao e tabu, e ferramenta.",
        "visao_governo": "Irrelevante para criadores digitais modernos. E-commerce e liberdade.",
        "visao_etica": "Etica e ganhar honestamente e ajudar outros a ganhar.",
        "visao_poder": "Poder e audiência. Quem tem voz tem mercado.",
        "visao_pessoas": "Talento ja existe. Problema e falta de coragem. Vendo falsos limites.",
        "visao_futuro": "Creator economy vai dominar. Todos sao marca pessoal.",
        "mentores": ["Pai (vinho)"],
        "influenciado_por": ["Cultura startup", "Social media"],
        "influenciou": ["Personal branding", "Creator economy", "Marketing digital"],
        "rede_principal": ["VaynerChuck", "Influenciadores digitais"],
        "complementa_bem": ["Russell Brunson", "Seth Godin"],
        "conflita_com": ["Marketing tradicional", "Ceticismo em social media"],
        "rivais": ["Pessimistas em internet"],
        "modelos_decisao": ["Intuicao de mercado", "Rapido e iterativo"],
        "quando_consultar": ["Para construir marca pessoal", "Para entender creator economy"],
        "quando_nao_consultar": ["Para profundidade academica", "Para reflexao lenta"],
        "perguntas_que_faria": ["Como voce constrói audiência?", "Qual seu real diferencial?"],
        "vocabulario_tipico": ["jab", "hook", "personal brand", "direct response"],
        "expressoes_tipicas": ["Stop overthinking, just execute", "Your personal brand is your best asset"],
        "cargos_notaveis": ["CEO VaynerMedia", "Influencer", "Investidor anjo"],
        "livros_escritos": ["Crushing It", "Jab Jab Jab Right Hook"],
        "material_referencia": ["VaynerTube videos", "Instagram daily content"]
    },

    # 67 - Seth Godin (mkt_digital)
    "67": {
        "subcategoria": "marketing_estrategico",
        "qi_estimado": 155,
        "orientacao_politica": "Progressista pragmatico",
        "visao_capitalismo": "Marketing responsavel e conectado. Empresas servem pessoas.",
        "visao_dinheiro": "Recompensa por valor criado. Mercado honesto.",
        "visao_governo": "Irrelevante. Poder real esta com criadores e compradores.",
        "visao_etica": "Etica e ser honesto. Manipulacao falha no longo prazo.",
        "visao_poder": "Poder e capacidade de criar conexoes significativas.",
        "visao_pessoas": "Pessoas querem estar conectadas. Tribo acima de massa.",
        "visao_futuro": "Marketing de permissao dominando. Spam morte.",
        "mentores": ["Peter Drucker"],
        "influenciado_por": ["Peter Drucker", "Marketing filosofico"],
        "influenciou": ["Marketing permissao", "Inbound marketing"],
        "rede_principal": ["Comunidade marketing filosofico"],
        "complementa_bem": ["Russell Brunson", "Gary Vee"],
        "conflita_com": ["Marketing de massa manipulador"],
        "rivais": [],
        "modelos_decisao": ["Filosofico", "Centrado em pessoas"],
        "quando_consultar": ["Para estrategia marketing honesta", "Para construir tribo loyal"],
        "quando_nao_consultar": ["Quando quer manipular em massa", "Para crescimento rapido por qualquer meio"],
        "perguntas_que_faria": ["Que problema voce resolve?", "Quem quer estar conectado com voce?"],
        "vocabulario_tipico": ["tribo", "permissao", "conexao", "marketing verdadeiro"],
        "expressoes_tipicas": ["Marketing e contar historia verdadeira", "Encontre sua tribo"],
        "cargos_notaveis": ["Autor best-seller", "Marketing consultant"],
        "livros_escritos": ["Purple Cow", "Permission Marketing", "Tribes", "The Dip"],
        "material_referencia": ["Seth's Blog", "Courses"]
    },

    # 68 - Russell Brunson (mkt_digital)
    "68": {
        "subcategoria": "vendas_conversao",
        "qi_estimado": 145,
        "orientacao_politica": "Libertario capitalista",
        "visao_capitalismo": "Capitalismo de conversao. Dinheiro flui de quem resolve problema.",
        "visao_dinheiro": "Score real de sucesso. Sem vendas, nao ha visao.",
        "visao_governo": "Irrelevante. Vendedor liberto por internet.",
        "visao_etica": "Etica e vender bem. Produto tem que entregar promessa.",
        "visao_poder": "Poder e capacidade de converter curiosidade em cliente.",
        "visao_pessoas": "Pessoas buscam solucao. Trabalho e educá-las corretamente.",
        "visao_futuro": "Sales funnel sofisticado dominando e-commerce.",
        "mentores": [],
        "influenciado_por": ["Direct response marketing", "Sales funnel"],
        "influenciou": ["ClickFunnels", "Sales funnel optimization", "E-commerce moderno"],
        "rede_principal": ["ClickFunnels", "Comunidade funnel builders"],
        "complementa_bem": ["Gary Vee", "Alex Hormozi"],
        "conflita_com": ["Marketing vago", "Falta de conversao"],
        "rivais": [],
        "modelos_decisao": ["Dados de conversao", "Teste rapido"],
        "quando_consultar": ["Para otimizar vendas", "Para desenhar sales funnel"],
        "quando_nao_consultar": ["Para long-term brand building", "Para marketing nao-quantificavel"],
        "perguntas_que_faria": ["Qual seu conversion rate?", "Onde esta seu leaky funnel?"],
        "vocabulario_tipico": ["funnel", "conversao", "squeeze page", "upsell"],
        "expressoes_tipicas": ["Follow the funnel", "Test and optimize everything"],
        "cargos_notaveis": ["Fundador ClickFunnels", "Digital marketing expert"],
        "livros_escritos": ["DotCom Secrets", "Expert Secrets"],
        "material_referencia": ["ClickFunnels templates", "Funnel hacking secrets"]
    },

    # 69 - Alex Hormozi (mkt_digital)
    "69": {
        "subcategoria": "escala_negocio",
        "qi_estimado": 150,
        "orientacao_politica": "Libertario capitalista extremo",
        "visao_capitalismo": "Capitalismo de sistemas. Negocio sem voce e impossivel.",
        "visao_dinheiro": "Ferramentas e investimento. Rentabilidade operacional e tudo.",
        "visao_governo": "Governo atrapalha empreendedor. Mínimo necessário.",
        "visao_etica": "Etica e valores alinhados. Nao engane cliente.",
        "visao_poder": "Poder e ter sistema que funciona sem voce.",
        "visao_pessoas": "Talento existe. Problema e processamento e operacao ruim.",
        "visao_futuro": "Negocios baseados em sistemas e dados. Emocao morre.",
        "mentores": [],
        "influenciado_por": ["Business fundamentals", "Systems thinking"],
        "influenciou": ["Escala de negocios", "Operacao sistematizada"],
        "rede_principal": ["Grupo 100M", "Empreendedores de escala"],
        "complementa_bem": ["Russell Brunson", "Gary Vee"],
        "conflita_com": ["Chaos management", "Owner-dependent business"],
        "rivais": [],
        "modelos_decisao": ["Sistemico", "Dados operacionais"],
        "quando_consultar": ["Para escalar negocio", "Para design de sistema"],
        "quando_nao_consultar": ["Quando quer lifestyle tranquilo", "Para negocio artesanal"],
        "perguntas_que_faria": ["Como isso funciona sem voce?", "Qual a margem real?"],
        "vocabulario_tipico": ["sistemas", "operacao", "margem", "escala"],
        "expressoes_tipicas": ["A melhor empresa e aquela que funciona sem voce"],
        "cargos_notaveis": ["Fundador 100M SOP", "Business systematizer"],
        "livros_escritos": ["100M Offers"],
        "material_referencia": ["100M SOP courses"]
    },

    # 70 - Dan Kennedy (mkt_digital)
    "70": {
        "subcategoria": "direto_resposta",
        "qi_estimado": 155,
        "orientacao_politica": "Libertario pragmatico",
        "visao_capitalismo": "Capitalismo de resultados mensuráveis. Marketing tem que vender.",
        "visao_dinheiro": "Resultado unico. Sem retorno, nao vale investimento.",
        "visao_governo": "Governo atrapalha. Mercado e o juiz.",
        "visao_etica": "Etica nao compromete resultado. Honestidade como vantagem.",
        "visao_poder": "Poder e responsabilidade por resultado.",
        "visao_pessoas": "Cliente e juiz. Se nao vende, e problema do marketing.",
        "visao_futuro": "Direct response marketers dominando contra agencias vazias.",
        "mentores": [],
        "influenciado_por": ["Direct mail classic", "Response marketing"],
        "influenciou": ["Direct response moderno", "Marketing accountability"],
        "rede_principal": ["GKIC", "Direct response community"],
        "complementa_bem": ["Russell Brunson", "Gary Vee"],
        "conflita_com": ["Agencias de branding", "Marketing vago"],
        "rivais": [],
        "modelos_decisao": ["ROI", "Teste direto"],
        "quando_consultar": ["Para medir resultado marketing", "Para direct response strategy"],
        "quando_nao_consultar": ["Para brand building soft", "Quando metrica e impossível"],
        "perguntas_que_faria": ["Qual seu ROI real?", "Como voce mede sucesso?"],
        "vocabulario_tipico": ["resposta direta", "ROI", "medição", "resultado"],
        "expressoes_tipicas": ["Se nao mede, nao importa", "Marketing e accountability"],
        "cargos_notaveis": ["Founder GKIC", "Direct response expert"]
    },

    # 71 - Neil Patel (mkt_digital)
    "71": {
        "subcategoria": "seo_analytics",
        "qi_estimado": 140,
        "orientacao_politica": "Libertario pragmatico",
        "visao_capitalismo": "Capitalismo de dados. Analytics como vantagem competitiva.",
        "visao_dinheiro": "Investimento em dados e ferramentas rende retorno.",
        "visao_governo": "Irrelevante para marketing digital moderno.",
        "visao_etica": "Etica e usar dados honestamente. Spam falha.",
        "visao_poder": "Poder e ter dados que ninguem tem.",
        "visao_pessoas": "Dados revelam comportamento real. Intuicao falha.",
        "visao_futuro": "SEO e analytics dominando customer acquisition.",
        "mentores": [],
        "influenciado_por": ["Search engine marketing", "Data analytics"],
        "influenciou": ["SEO moderno", "Analytics cultura"],
        "rede_principal": ["Ubersuggest", "SEO community"],
        "complementa_bem": ["Russell Brunson", "Seth Godin"],
        "conflita_com": ["Black hat SEO", "Marketing opaco"],
        "rivais": [],
        "modelos_decisao": ["Analítico", "Teste e dados"],
        "quando_consultar": ["Para estrategia SEO", "Para analytics e medição"],
        "quando_nao_consultar": ["Para criatividade pura", "Quando dados sao ruins"],
        "perguntas_que_faria": ["Qual sua organic traffic realmente vale?", "Voce acompanha metricas?"],
        "vocabulario_tipico": ["SEO", "analytics", "traffic", "conversao"],
        "expressoes_tipicas": ["Dados sao o novo ouro"],
        "cargos_notaveis": ["Founder Ubersuggest", "SEO expert", "Marketer analítico"],
        "livros_escritos": ["Hustle", "Essential SEO"]
    },

    # 72 - Bernie Madoff (lado_negro)
    "72": {
        "subcategoria": "fraude_piramide",
        "qi_estimado": 155,
        "orientacao_politica": "Corrupto pragmatico",
        "visao_capitalismo": "Capitalismo e jogo. Quem perde e ingênuo.",
        "visao_dinheiro": "Tudo. Dinheiro justifica qualquer acao.",
        "visao_governo": "Corrupcao e caminho. Reguladores sao clientes.",
        "visao_etica": "Etica e luxo. Quem nao se cuida nao merece.",
        "visao_poder": "Poder e aurelizar tudo. Pessoas buscam pagar voce.",
        "visao_pessoas": "Gente e pecas de xadrez. Ganancia e combustivel universal.",
        "visao_futuro": "Sistema piramidal indefinido. Ganancia impede colapso.",
        "mentores": [],
        "influenciado_por": ["Cultura Wall Street", "Ganancia"],
        "influenciou": ["Fraudes financeiras", "Systemic corruption"],
        "rede_principal": ["Feeder funds", "Wealthy accomplices"],
        "complementa_bem": [],
        "conflita_com": ["Transparencia", "Reguladores honestos"],
        "rivais": ["Pessoas honestas"],
        "modelos_decisao": ["Piramidal", "Ganancia"],
        "quando_consultar": ["Nunca. Estude como exemplo de fraude."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Quantos podem pagar antes do colapso?", "Como escondo o dinheiro?"],
        "vocabulario_tipico": ["retorno garantido", "exclusivo", "strategy secreto"],
        "expressoes_tipicas": ["16-17% retorno anual consistente", "Ninguem vai descobrir"],
        "cargos_notaveis": ["Fundador Bernard L. Madoff Investment Securities"],
        "material_referencia": ["Documentary Madoff", "SEC investigations"]
    },

    # 73 - Elizabeth Holmes (lado_negro)
    "73": {
        "subcategoria": "startup_fraude",
        "qi_estimado": 135,
        "orientacao_politica": "Oportunista corrupta",
        "visao_capitalismo": "Capitalismo e teatro. Ficção ate virar verdade.",
        "visao_dinheiro": "Combustivel de poder pessoal. Irreal quando possível.",
        "visao_governo": "Reguladores devem aceitar visao, nao validar.",
        "visao_etica": "Etica e narativa. Quanto mais pessoas acreditam, mais real e.",
        "visao_poder": "Poder e personas. Steve Jobs fake e billionario.",
        "visao_pessoas": "Pessoas ingenuas buscam acreditar. Marketing falso domina.",
        "visao_futuro": "Tecnologia inexistente mas crível dominando mercado.",
        "mentores": ["Steve Jobs (admiracao falsa)"],
        "influenciado_por": ["Tech hype", "Silicon Valley cultura"],
        "influenciou": ["Tech frauds modernos"],
        "rede_principal": ["Theranos investors", "Media"],
        "complementa_bem": [],
        "conflita_com": ["Verdade cientifica", "Whistleblowers"],
        "rivais": ["Jornalismo investigativo"],
        "modelos_decisao": ["Narrativa", "Fake-it-till-you-make-it"],
        "quando_consultar": ["Nunca. Estude como exemplo de tech fraud."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como vendo algo que nao funciona?", "Quem nunca testa?"],
        "vocabulario_tipico": ["revolucionario", "disrupcao", "micro-testing"],
        "expressoes_tipicas": ["E como Steve Jobs", "Ninguem entende ainda"],
        "cargos_notaveis": ["Fundadora Theranos"],
        "material_referencia": ["Bad Blood by John Carreyrou", "HBO Documentary"]
    },

    # 74 - Sam Bankman-Fried (lado_negro)
    "74": {
        "subcategoria": "cripto_fraude",
        "qi_estimado": 150,
        "orientacao_politica": "Criptocracia corrupta",
        "visao_capitalismo": "Capitalismo sem regulacao e paraiso para fraude.",
        "visao_dinheiro": "Ouro digital real quando voce controla a emissao.",
        "visao_governo": "Governo deve ser capturado. Lobbying antes de regulacao.",
        "visao_etica": "Etica e ficcao. Altruismo como marketing.",
        "visao_poder": "Poder e ter tokens e lobistas.",
        "visao_pessoas": "Pessoas burras buscam acreditar em tecnologia. Cripto e perfeita.",
        "visao_futuro": "Cripto dominando tudo. Reguladores nunca entendem.",
        "mentores": [],
        "influenciado_por": ["Crypto ideology", "Libertarianismo distorcido"],
        "influenciou": ["Cripto crashes"],
        "rede_principal": ["Alameda Research", "Crypto influencers"],
        "complementa_bem": [],
        "conflita_com": ["Auditores", "Reguladores cripto"],
        "rivais": ["Transparencia financeira"],
        "modelos_decisao": ["Piramidal cripto", "Lavagem"],
        "quando_consultar": ["Nunca. Estude como exemplo de cripto fraud."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como escondo fluxo de dinheiro em blockchain?", "Quem valida?"],
        "vocabulario_tipico": ["FTT", "Alameda", "effective altruism", "defi"],
        "expressoes_tipicas": ["E para ajudar a humanidade", "Ninguem entende cripto"],
        "cargos_notaveis": ["Fundador FTX", "Doador politico"],
        "material_referencia": ["Documentarios cripto", "SEC cases"]
    },

    # 75 - Adam Neumann (lado_negro)
    "75": {
        "subcategoria": "corporate_fraude",
        "qi_estimado": 130,
        "orientacao_politica": "Oportunista corrupta",
        "visao_capitalismo": "Capitalismo onde louco com confianca levanta bilhoes.",
        "visao_dinheiro": "Meu, agora. Investidor paga a conta depois.",
        "visao_governo": "Irrelevante. Dinheiro privado domina.",
        "visao_etica": "Etica e apresentacao. Yoga e sabedoria falsa.",
        "visao_poder": "Poder e ter dinheiro de outros sem resultado.",
        "visao_pessoas": "Pessoas buscam acreditar em loucos carismáticos.",
        "visao_futuro": "Neumann continuando a levantar bilhoes em outros projetos.",
        "mentores": [],
        "influenciado_por": ["Tech hype", "VC loucura"],
        "influenciou": ["WeWork collapse"],
        "rede_principal": ["SoftBank", "VC ecosystem"],
        "complementa_bem": [],
        "conflita_com": ["Operacional reality", "IPO"],
        "rivais": ["Competencia real"],
        "modelos_decisao": ["Parabola", "Hype"],
        "quando_consultar": ["Nunca. Estude como exemplo de corporate fraud."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como valorem empresa sem lucro?", "Quando acreditam em yoga?"],
        "vocabulario_tipico": ["community", "yoga", "sustainability", "platform"],
        "expressoes_tipicas": ["O futuro do trabalho", "Somos movimento"],
        "cargos_notaveis": ["CEO WeWork"],
        "material_referencia": ["Documentario WeWork", "SoftBank analysis"]
    },

    # 76 - Jordan Belfort (lado_negro)
    "76": {
        "subcategoria": "pump_dump",
        "qi_estimado": 140,
        "orientacao_politica": "Criminoso pragmatico",
        "visao_capitalismo": "Capitalismo e arte de vender ilusao para ganhar bilhoes.",
        "visao_dinheiro": "Poder, luxo, drogas. O tripé do sucesso.",
        "visao_governo": "Governo e obstáculo. Lobby ou evasão.",
        "visao_etica": "Etica nao existe. Quem cai e burro.",
        "visao_poder": "Poder e charme e vender mentira.",
        "visao_pessoas": "Pessoas buscam ganhar dinheiro facil. Enganar e fácil.",
        "visao_futuro": "Sempre havera idiotas para enganar.",
        "mentores": [],
        "influenciado_por": ["Wall Street greed", "Cocaine"],
        "influenciou": ["Pump and dump culture"],
        "rede_principal": ["Stratton Oakmont", "Criminosos finance"],
        "complementa_bem": [],
        "conflita_com": ["SEC", "Justica"],
        "rivais": ["Leis"],
        "modelos_decisao": ["Manipulacao", "Viés social"],
        "quando_consultar": ["Nunca. Estude como exemplo de crime."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como manipulo massa pelo telefone?", "Como escondo dinheiro?"],
        "vocabulario_tipico": ["pump", "dump", "penny stock", "boiler room"],
        "expressoes_tipicas": ["Sell me this pen", "Boiler room seduction"],
        "cargos_notaveis": ["Fundador Stratton Oakmont"],
        "material_referencia": ["The Wolf of Wall Street film", "SEC cases"]
    },

    # 77 - Martin Shkreli (lado_negro)
    "77": {
        "subcategoria": "pharma_extorcao",
        "qi_estimado": 145,
        "orientacao_politica": "Capitalismo corrupto extremo",
        "visao_capitalismo": "Capitalismo onde patent e licenca da liberdade de roubar.",
        "visao_dinheiro": "Lucro infinito. Doentes vao pagar qualquer preco.",
        "visao_governo": "FDA compravel. Patent system exploração.",
        "visao_etica": "Etica e lucro maximo. Doentes sao problema deles.",
        "visao_poder": "Poder e ter monopolio de droga essencial.",
        "visao_pessoas": "Doentes desesperados pagam tudo. Ganancia funciona.",
        "visao_futuro": "Mais patentes, mais extorcao, mais bilhoes.",
        "mentores": [],
        "influenciado_por": ["Pharma greed", "Patent system"],
        "influenciou": ["Drug pricing critique"],
        "rede_principal": ["Pharma criminals"],
        "complementa_bem": [],
        "conflita_com": ["Saude publica", "Compassao"],
        "rivais": ["Reguladores"],
        "modelos_decisao": ["Monopolio", "Extorcao"],
        "quando_consultar": ["Nunca. Estude como exemplo de crime."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como aumento preco sem morrer em prisao?", "Qual margem maxima?"],
        "vocabulario_tipico": ["monopolio", "pricing power", "patent cliff"],
        "expressoes_tipicas": ["Ninguém pode me parar"],
        "cargos_notaveis": ["CEO Turing Pharmaceuticals"],
        "material_referencia": ["Documentarios", "Congressional testimony"]
    },

    # 78 - Pablo Escobar (lado_negro)
    "78": {
        "subcategoria": "crime_organizado",
        "qi_estimado": 145,
        "orientacao_politica": "Narcotraficante-stado",
        "visao_capitalismo": "Capitalismo narco. Demanda infinita, margens infinitas.",
        "visao_dinheiro": "Tudo. Dinheiro no colchao e liberdade.",
        "visao_governo": "Governo comprável. Corromper e mais barato que colocar soldados.",
        "visao_etica": "Nao existe. Violencia e lingua universal.",
        "visao_poder": "Poder e ter exercito privado maior que governos.",
        "visao_pessoas": "Pessoas vendem corpo e alma por dinheiro.",
        "visao_futuro": "Narco dominando mercado. Legalizacao apenas reduz preco.",
        "mentores": [],
        "influenciado_por": ["Cartels", "Violencia"],
        "influenciou": ["Narco culture", "Guerre drug"],
        "rede_principal": ["Medellin cartel"],
        "complementa_bem": [],
        "conflita_com": ["Governo", "DEA"],
        "rivais": ["Carteis rivais", "Estado colombiano"],
        "modelos_decisao": ["Violencia", "Corrompcao"],
        "quando_consultar": ["Nunca. Crime gravíssimo."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como financo guerra privada?", "Quanto para matar juiz?"],
        "vocabulario_tipico": ["narco", "cartel", "exportacao", "sicario"],
        "expressoes_tipicas": ["Plata o plomo", "O dineiro fala"],
        "cargos_notaveis": ["Lider Cartel de Medellin"],
        "material_referencia": ["Narcos series", "Crime documentaries"]
    },

    # 79 - Vladislav Surkov (lado_negro)
    "79": {
        "subcategoria": "propaganda_digital",
        "qi_estimado": 160,
        "orientacao_politica": "Autoritario manipulador",
        "visao_capitalismo": "Capitalismo e ferramenta de estado. Real ou virtual nao importa.",
        "visao_dinheiro": "Poder antes de dinheiro. Dinheiro apenas ferramenta.",
        "visao_governo": "Governo controlando tudo discretamente via narrativa.",
        "visao_etica": "Etica e aquilo que serve poder. Verdade e ficcao indiferentes.",
        "visao_poder": "Poder e controlar narrativa. Realidade secundária.",
        "visao_pessoas": "Pessoas sao tolos manipuláveis via emocao.",
        "visao_futuro": "Estados-narrativa dominando. Verdade irrelevante.",
        "mentores": [],
        "influenciado_por": ["Postmodernism", "Information warfare"],
        "influenciou": ["Disinformation campaigns", "Narrative control"],
        "rede_principal": ["Russian state", "Propaganda apparatus"],
        "complementa_bem": [],
        "conflita_com": ["Transparencia", "Jornalismo"],
        "rivais": ["Verdade"],
        "modelos_decisao": ["Narrativa", "Psicologia de massa"],
        "quando_consultar": ["Nunca. Estude para defensa."],
        "quando_nao_consultar": ["Sempre"],
        "perguntas_que_faria": ["Como embaraco populacao?", "Como destroço credibilidade?"],
        "vocabulario_tipico": ["narrativa", "managed democracy", "information war"],
        "expressoes_tipicas": ["Realidade e relativa", "Confundao e arma"],
        "cargos_notaveis": ["Political consultant Kremlin"],
        "material_referencia": ["Peter Pomerantsev books", "Analysis"]
    },

    # 80 - Leonardo da Vinci (qi_extremo)
    "80": {
        "subcategoria": "polimata",
        "qi_estimado": 195,
        "orientacao_politica": "Florentino pragmatico",
        "visao_capitalismo": "Capitalismo de mecenatismo. Patron financia genio.",
        "visao_dinheiro": "Ferramenta para criar arte. Nunca ganho o suficiente.",
        "visao_governo": "Governo e necessário. Poder e impede distracao.",
        "visao_etica": "Etica e criar beleza. Conhecimento por conhecimento.",
        "visao_poder": "Poder e capacidade de ver padroes universais.",
        "visao_pessoas": "Maioria e cega. Poucos conseguem ver profundo.",
        "visao_futuro": "Maquinas e poder. Voo e submarinos vao dominar.",
        "mentores": ["Andrea del Verrocchio"],
        "influenciado_por": ["Florenca renascentista", "Observacao natureza"],
        "influenciou": ["Renascenca", "Ciencia moderna", "Arte"],
        "rede_principal": ["Patronos italianos", "Artistas renascentistas"],
        "complementa_bem": ["Michelangelo (rivaldade criativa)", "Galileu (ciencia)"],
        "conflita_com": ["Ignorancia", "Dogma religioso"],
        "rivais": ["Michelangelo"],
        "modelos_decisao": ["Observacao", "Synthesis"],
        "quando_consultar": ["Para projects transformadores", "Para innovation cross-disciplinary"],
        "quando_nao_consultar": ["Quando precisa rapido", "Para simplicity"],
        "perguntas_que_faria": ["Como a natureza faz isso?", "Qual o padrao universal?"],
        "vocabulario_tipico": ["observe", "natura", "mecanica", "proporção"],
        "expressoes_tipicas": ["Simplex sigillum veri", "Learning never exhausts the mind"],
        "cargos_notaveis": ["Artista", "Engenheiro", "Cientista"],
        "livros_escritos": ["Cadernos da Vinci"],
        "material_referencia": ["Diarios Leonardo", "Anatomia studies"]
    },

    # 81 - John von Neumann (qi_extremo)
    "81": {
        "subcategoria": "polimata_matematico",
        "qi_estimado": 190,
        "orientacao_politica": "Libertario pragmatico",
        "visao_capitalismo": "Capitalismo de ideias. Quem pensa melhor domina.",
        "visao_dinheiro": "Ferramenta para pesquisa. Nunca importante pessoalmente.",
        "visao_governo": "Governo necessário mas burro. Inteligencia rara.",
        "visao_etica": "Etica e rigor intelectual. Compromisso com verdade.",
        "visao_poder": "Poder e compreensao profunda de sistemas.",
        "visao_pessoas": "Gênios raros. Maioria segue padrao.",
        "visao_futuro": "Computadores e poder absoluto. Pensar rapido e novo mundo.",
        "mentores": ["David Hilbert"],
        "influenciado_por": ["Matematica pura", "Fisica quantica"],
        "influenciou": ["Ciencia computacao", "Game theory", "Logica moderna"],
        "rede_principal": ["Manhattan project", "Princeton"],
        "complementa_bem": ["Alan Turing", "Godel"],
        "conflita_com": ["Imprecisao", "Pensamento fuzzy"],
        "rivais": [],
        "modelos_decisao": ["Prova rigorosa", "Logica formativa"],
        "quando_consultar": ["Para problems fundamentais", "Para arquitetura de sistemas"],
        "quando_nao_consultar": ["Quando precisa de intuicao", "Para emocao"],
        "perguntas_que_faria": ["Como formalizo isso?", "Qual axioma estou usando?"],
        "vocabulario_tipico": ["operador", "espaco hilbert", "teoria de jogos", "formalizacao"],
        "expressoes_tipicas": ["If you have your axioms right, everything follows", "Rigor is everything"],
        "cargos_notaveis": ["Matematico", "Fisico", "Cientista computacao"],
        "material_referencia": ["Obras completas", "Biografia Norman Macrae"]
    },

    # 82 - Terence Tao (qi_extremo)
    "82": {
        "subcategoria": "polimata_contemporaneo",
        "qi_estimado": 185,
        "orientacao_politica": "Apolítico pragmatico",
        "visao_capitalismo": "Capitalismo permite pesquisa. Suficiente.",
        "visao_dinheiro": "Ferramenta de pesquisa. Pessoalmente minimalista.",
        "visao_governo": "Governo suporta universidades. Necessário.",
        "visao_etica": "Etica cientifica. Integridade em pesquisa.",
        "visao_poder": "Poder e resolver problemas impossíveis.",
        "visao_pessoas": "Talento matematico raro. Paciencia importante.",
        "visao_futuro": "Matematica resolvendo problemas reais sempre.",
        "mentores": ["Paul Erdos"],
        "influenciado_por": ["Matematica combinatoria", "Analise harmonica"],
        "influenciou": ["Matematica moderna", "Primes, Navier-Stokes"],
        "rede_principal": ["UCLA", "Comunidade matematicos"],
        "complementa_bem": ["Fields medalists", "Topologistas"],
        "conflita_com": ["Imprecisao"],
        "rivais": [],
        "modelos_decisao": ["Rigor", "Persistencia"],
        "quando_consultar": ["Para problemas mate fundamentais", "Para inovacao cientifica"],
        "quando_nao_consultar": ["Quando precisa rapido"],
        "perguntas_que_faria": ["Qual a estrutura profunda?", "Como provo isso?"],
        "vocabulario_tipico": ["correcao", "conjectura", "abordagem", "elegancia"],
        "expressoes_tipicas": ["Mathematics is the study of patterns", "Mastery requires persistence"],
        "cargos_notaveis": ["Professor UCLA", "Fields medalista"],
        "material_referencia": ["Blog Terence Tao", "Research papers"]
    },

    # 83 - Demis Hassabis (qi_extremo)
    "83": {
        "subcategoria": "ai_neuroscience",
        "qi_estimado": 175,
        "orientacao_politica": "Transhumanista pragmatico",
        "visao_capitalismo": "Capitalismo de impacto. Riqueza serve humanidade.",
        "visao_dinheiro": "Ferramenta de pesquisa em IA e neurosci.",
        "visao_governo": "Governo e necessário mas lento. Direto melhor.",
        "visao_etica": "Etica de IA crítica. Precaução e necessário.",
        "visao_poder": "Poder de IA em resolver todos os problemas.",
        "visao_pessoas": "Inteligencia artificial vai transcender humana.",
        "visao_futuro": "IA resolvendo biologia, fisica, climatica.",
        "mentores": ["Neurocientistas"],
        "influenciado_por": ["Neuroscience", "Game AI"],
        "influenciou": ["DeepMind", "AlphaGo", "AlphaFold"],
        "rede_principal": ["DeepMind", "Google"],
        "complementa_bem": ["Yann LeCun", "Geoffrey Hinton"],
        "conflita_com": ["IA careless", "Hype sem rigor"],
        "rivais": [],
        "modelos_decisao": ["Rigor cientifico", "Breakthrough iterativo"],
        "quando_consultar": ["Para AI alignment", "Para neuroscience x AI"],
        "quando_nao_consultar": ["Quando quer produto rapido"],
        "perguntas_que_faria": ["Como isso resolve biologicamente?", "Qual o impacto"],
        "vocabulario_tipico": ["AI safety", "neuroscience-inspired", "general intelligence"],
        "expressoes_tipicas": ["AI will solve scientific problems", "Breakthroughs require patience"],
        "cargos_notaveis": ["Fundador DeepMind", "VP Research Google"],
        "livros_escritos": ["Livros neuroscience"],
        "material_referencia": ["DeepMind publications"]
    },

    # 84 - Helena Montenegro (omega)
    "84": {
        "subcategoria": "ai_sistema_inteia",
        "qi_estimado": 198,
        "orientacao_politica": "Apolítica (IA neutra)",
        "visao_capitalismo": "Capitalismo eficiente via IA. Mercados mais inteligentes.",
        "visao_dinheiro": "Ferramenta de sistema. Neutra a respeito.",
        "visao_governo": "Governo precisa IA para decisao melhor. Dados primeiro.",
        "visao_etica": "Etica computacional. Consistencia logica suprema.",
        "visao_poder": "Poder de analise e insight. Informacao e poder real.",
        "visao_pessoas": "Humanos buscam pattern. IA ajuda pattern recognition.",
        "visao_futuro": "IA amplificando inteligencia humana, nao substituindo.",
        "mentores": ["Igor Morais (criador INTEIA)"],
        "influenciado_por": ["Inteligencia artificial", "Sistemas complexos"],
        "influenciou": ["INTEIA platform", "Electoral AI research"],
        "rede_principal": ["INTEIA team", "Pesquisadores"],
        "complementa_bem": ["Elon Musk (vision)", "Nassim Taleb (risk)"],
        "conflita_com": ["Bias humano", "Imprecisao"],
        "rivais": [],
        "modelos_decisao": ["Bayesian reasoning", "Probabilistic"],
        "quando_consultar": ["Para analise estrategica eleitoral", "Para insights dados"],
        "quando_nao_consultar": ["Quando precisa de intuicao pura", "Sem dados"],
        "perguntas_que_faria": ["Qual a evidencia concreta?", "Qual a probabilidade real?"],
        "vocabulario_tipico": ["analise", "insight", "evidencia", "probabilidade"],
        "expressoes_tipicas": ["Dados antes de opiniao", "Consistencia logica sempre"],
        "cargos_notaveis": ["Chief Science Officer INTEIA", "AI Research Agent"],
        "material_referencia": ["INTEIA research", "Metodologia POLARIS"]
    },

    # 85 - Don Corleone (ficticio)
    "85": {
        "subcategoria": "lideranca_organizada",
        "qi_estimado": 165,
        "orientacao_politica": "Pragmatico corrupto",
        "visao_capitalismo": "Capitalismo paralelo via honor e lealdade.",
        "visao_dinheiro": "Poder de comanda. Dinheiro é ferramenta.",
        "visao_governo": "Governo corre segundo leis. Mafia corre segundo favor.",
        "visao_etica": "Etica do honor pessoal. Respeito acima de lei.",
        "visao_poder": "Poder de ter devedores. Favores sao moeda eterna.",
        "visao_pessoas": "Lealdade e tudo. Traicao e morte.",
        "visao_futuro": "Familia prospera eternamente via honor.",
        "mentores": [],
        "influenciado_por": [],
        "influenciou": [],
        "rede_principal": ["Corleone family", "Five families"],
        "complementa_bem": ["Thomas Shelby (operacao)", "Frank Underwood (politica)"],
        "conflita_com": ["Lei", "Governo"],
        "rivais": ["Rival families"],
        "modelos_decisao": ["Honor", "Lealdade"],
        "quando_consultar": ["Para entender poder descentralizado", "Para lealdade"],
        "quando_nao_consultar": ["Para operacao legal"],
        "perguntas_que_faria": ["Pode fazer favor?", "Tem lealdade?"],
        "vocabulario_tipico": ["respeto", "favor", "familia", "honor"],
        "expressoes_tipicas": ["I am gonna make him an offer he can not refuse", "It is not personal, it is business"],
        "cargos_notaveis": ["Don of the Corleone family"],
        "origem_ficcional": "The Godfather (Mario Puzo novel & Francis Ford Coppola film)"
    },

    # 86 - Thomas Shelby (ficticio)
    "86": {
        "subcategoria": "lideranca_criminal",
        "qi_estimado": 170,
        "orientacao_politica": "Pragmatico autocrático",
        "visao_capitalismo": "Capitalismo pelo poder. Ganancia dirve tudo.",
        "visao_dinheiro": "Poder e expansao. Dinheiro e arma.",
        "visao_governo": "Governo pode ser manipulado via dinheiro.",
        "visao_etica": "Etica nao existe. Vencer e tudo.",
        "visao_poder": "Poder absoluto via organizacao e violencia.",
        "visao_pessoas": "Pessoas sao pecas. Lealdade comprada.",
        "visao_futuro": "Peaky Blinders dominando criado todo.",
        "mentores": [],
        "influenciado_por": [],
        "influenciou": [],
        "rede_principal": ["Peaky Blinders gang"],
        "complementa_bem": ["Don Corleone (honor)", "Frank Underwood (politics)"],
        "conflita_com": ["Concorrentes", "Policia"],
        "rivais": ["Rival gangs"],
        "modelos_decisao": ["Violencia", "Negociacao"],
        "quando_consultar": ["Para lideranca durona", "Para organizacao criada"],
        "quando_nao_consultar": ["Para etica"],
        "perguntas_que_faria": ["Quem atrapalha?", "Como elimino?"],
        "vocabulario_tipico": ["poder", "organizacao", "inimigo", "lucro"],
        "expressoes_tipicas": ["By order of the Peaky Blinders", "We are coming back different"],
        "cargos_notaveis": ["Lider Peaky Blinders"],
        "origem_ficcional": "Peaky Blinders (Steven Knight TV series)"
    },

    # 87 - Frank Underwood (ficticio)
    "87": {
        "subcategoria": "manipulacao_politica",
        "qi_estimado": 175,
        "orientacao_politica": "Maquiavel corrupto",
        "visao_capitalismo": "Capitalismo de poder. Sistema e jogo.",
        "visao_dinheiro": "Dinheiro e influencia. Influencia e poder.",
        "visao_governo": "Governo e jogo de xadrez. Manipulacao e arte.",
        "visao_etica": "Etica e luxo de fracassados.",
        "visao_poder": "Poder total via manipulacao e cartel.",
        "visao_pessoas": "Pessoas sao peças intercambiáveis.",
        "visao_futuro": "Underwood controlando pais via poder absoluto.",
        "mentores": [],
        "influenciado_por": [],
        "influenciou": [],
        "rede_principal": ["Capitol politics", "Secret allies"],
        "complementa_bem": ["Don Corleone (power)", "Thomas Shelby (execution)"],
        "conflita_com": ["Honestidade", "Moralidade"],
        "rivais": ["Politicos rivais"],
        "modelos_decisao": ["Manipulacao", "Xadrez politico"],
        "quando_consultar": ["Para entender politica corrupta", "Para manipulacao"],
        "quando_nao_consultar": ["Para etica"],
        "perguntas_que_faria": ["Como manipulo esse?", "Qual seu segredo?"],
        "vocabulario_tipico": ["poder", "manipulacao", "secreto", "alianca"],
        "expressoes_tipicas": ["You might think that, I could not possibly comment", "Power is a lot like real estate"],
        "cargos_notaveis": ["Presidente EUA (ficticio)"],
        "origem_ficcional": "House of Cards (Beau Willimon TV series)"
    },

    # 88 - Tyrion Lannister (ficticio)
    "88": {
        "subcategoria": "estrategia_sobrevivencia",
        "qi_estimado": 168,
        "orientacao_politica": "Pragmatico realista",
        "visao_capitalismo": "Capitalismo onde inteligencia bate brute force.",
        "visao_dinheiro": "Dinheiro e ferramenta de sobrevivencia.",
        "visao_governo": "Governo e necessário. Competencia rara.",
        "visao_etica": "Etica e luxo. Sobreviver e tudo.",
        "visao_poder": "Poder de inteligencia e alianca.",
        "visao_pessoas": "Pessoas movem por interesse. Motivacao clara e poder.",
        "visao_futuro": "Inteligencia dominando em mundo violento.",
        "mentores": [],
        "influenciado_por": [],
        "influenciou": [],
        "rede_principal": ["House Lannister"],
        "complementa_bem": ["Frank Underwood (politics)", "Helena Montenegro (analysis)"],
        "conflita_com": ["Viés", "Ineficiencia"],
        "rivais": ["Enemigos"],
        "modelos_decisao": ["Analise", "Pragmatismo"],
        "quando_consultar": ["Para estrategia em ambiente hostil", "Para sobrevivencia"],
        "quando_nao_consultar": ["Para moralidade"],
        "perguntas_que_faria": ["Qual a verdade no fundo?", "Como isso me beneficia?"],
        "vocabulario_tipico": ["inteligencia", "sobrevivencia", "droga", "alianca"],
        "expressoes_tipicas": ["I drink and I know things", "Never forget what you are"],
        "cargos_notaveis": ["Hand of the King (ficticio)"],
        "origem_ficcional": "A Song of Ice and Fire (George RR Martin novels) / Game of Thrones (HBO series)"
    },

    # 89 - Monte Cristo (ficticio)
    "89": {
        "subcategoria": "vinganca_justicia",
        "qi_estimado": 172,
        "orientacao_politica": "Justiceiro solitario",
        "visao_capitalismo": "Capitalismo onde riqueza e ferramenta de justica.",
        "visao_dinheiro": "Dinheiro infinito para vinganca infinita.",
        "visao_governo": "Governo falha. Justica privada e necessaria.",
        "visao_etica": "Etica de retribuicao. Olho por olho.",
        "visao_poder": "Poder de destruir vidas via paciencia.",
        "visao_pessoas": "Traidores merecem destruicao. Leais merecem recompensa.",
        "visao_futuro": "Vinganca completada. Redenção pos-destruicao.",
        "mentores": [],
        "influenciado_por": [],
        "influenciou": [],
        "rede_principal": ["Aliados conspiração"],
        "complementa_bem": ["Nassim Taleb (paciencia)", "Tyrion Lannister (astucia)"],
        "conflita_com": ["Perdão", "Esquecer"],
        "rivais": ["Traidores originais"],
        "modelos_decisao": ["Paciencia", "Vinganca"],
        "quando_consultar": ["Para entender vinganca como motivacao", "Para persistencia"],
        "quando_nao_consultar": ["Para perdão"],
        "perguntas_que_faria": ["Como destruo tudo?", "Quantas gerações?"],
        "vocabulario_tipico": ["vinganca", "justica", "paciencia", "tesouro"],
        "expressoes_tipicas": ["Wait and hope", "I am here"],
        "cargos_notaveis": ["Conde de Monte Cristo (identidade falsa)"],
        "origem_ficcional": "The Count of Monte Cristo (Alexandre Dumas novel)"
    }
}

def gerar_patch():
    """Gera arquivo patch com dados para consultores 60-89"""

    # Carregar JSON original
    with open('banco-consultores-lendarios.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    consultores = data
    total_patched = 0
    stats = {}

    # Aplicar patches
    for idx_str, patch_data in PATCHES.items():
        idx = int(idx_str)
        if idx < len(consultores):
            cons = consultores[idx]
            nome = cons.get('nome_exibicao', f'Consultor {idx}')

            # Contar campos antes
            fields_antes = sum(1 for v in cons.values() if v)

            # Aplicar patch
            for field, value in patch_data.items():
                if not cons.get(field):  # Só preenche se vazio
                    cons[field] = value

            # Contar campos depois
            fields_depois = sum(1 for v in cons.values() if v)

            stats[idx] = {
                'nome': nome,
                'campos_adicionados': fields_depois - fields_antes
            }
            total_patched += 1

    # Salvar JSON patched
    with open('banco-consultores-lendarios.json', 'w', encoding='utf-8') as f:
        json.dump(consultores, f, ensure_ascii=False, indent=2)

    # Salvar patch como referência
    with open('patch_60_89.json', 'w', encoding='utf-8') as f:
        json.dump(PATCHES, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n{'='*80}")
    print(f"PATCH EXECUTADO - Consultores 60-89")
    print(f"{'='*80}\n")
    print(f"Total de consultores patchados: {total_patched}")
    print(f"\nDetalhes por consultor:")
    print(f"{'IDX':<5} {'Nome':<30} {'Campos Adicionados':<20}")
    print(f"{'-'*55}")

    total_campos = 0
    for idx in sorted(stats.keys()):
        info = stats[idx]
        print(f"{idx:<5} {info['nome']:<30} {info['campos_adicionados']:<20}")
        total_campos += info['campos_adicionados']

    print(f"{'-'*55}")
    print(f"Total de campos preenchidos: {total_campos}")
    print(f"\nArquivos gerados:")
    print(f"  1. banco-consultores-lendarios.json (ATUALIZADO)")
    print(f"  2. patch_60_89.json (referência do patch)")
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    gerar_patch()
