"""
Campus INTEIA - Mapa do Think Tank.

O Campus é um grafo de localizações conectadas onde os consultores lendários
vivem, trabalham e interagem. Cada local tem propriedades que atraem
diferentes perfis de consultores.

Estrutura:
    Campus
    ├── Ágora Central (praça aberta - debates livres)
    ├── Torre de Estratégia (salas de guerra, planejamento)
    ├── Biblioteca Infinita (pesquisa, estudo, reflexão)
    ├── Café dos Filósofos (conversas informais)
    ├── Arena de Debates (debates estruturados)
    ├── Jardim dos Visionários (ideação criativa)
    ├── Tribunal da Razão (análise jurídica, ética)
    ├── Laboratório de Ideias (inovação, experimentação)
    ├── Galeria dos Legados (homenagem, inspiração)
    ├── Sala de Guerra (crise, decisões urgentes)
    ├── Auditório INTEIA (apresentações, palestras)
    ├── Ateliê dos Artesãos (criação, prototipagem)
    ├── Observatório do Futuro (tendências, previsões)
    ├── Residências Norte (visionários, tech, investidores)
    ├── Residências Sul (políticos, juristas, líderes)
    ├── Residências Leste (filósofos, psicólogos, espirituais)
    ├── Residências Oeste (estrategistas, negociadores, marketing)
    ├── Refeitório Central (refeições, socialização)
    └── Terraço Panorâmico (contemplação, networking)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Local:
    """Um local no Campus INTEIA."""

    id: str
    nome: str
    descricao: str
    tipo: str  # "publico", "trabalho", "residencia", "lazer", "especial"
    capacidade: int = 20
    categorias_afinidade: list[str] = field(default_factory=list)
    horario_pico: tuple[int, int] = (9, 18)  # hora início, hora fim
    nivel_formalidade: int = 5  # 1-10
    nivel_energia: int = 5  # 1-10
    conexoes: list[str] = field(default_factory=list)  # IDs dos locais conectados
    objetos: list[str] = field(default_factory=list)  # Objetos/recursos no local
    posicao_x: float = 0.0  # Coordenadas para visualização
    posicao_y: float = 0.0

    @property
    def esta_aberto(self) -> bool:
        """Locais residenciais sempre abertos, outros verificam horário."""
        return self.tipo == "residencia"

    def afinidade_consultor(self, categorias_consultor: list[str]) -> float:
        """Calcula afinidade de um consultor com este local (0-1)."""
        if not self.categorias_afinidade:
            return 0.5  # neutro
        matches = set(categorias_consultor) & set(self.categorias_afinidade)
        return len(matches) / max(len(self.categorias_afinidade), 1)


# ============================================================
# DEFINIÇÃO DO CAMPUS INTEIA
# ============================================================

LOCAIS: dict[str, Local] = {}


def _registrar(local: Local) -> Local:
    LOCAIS[local.id] = local
    return local


# --- ESPAÇOS PÚBLICOS ---

_registrar(Local(
    id="agora",
    nome="Ágora Central",
    descricao=(
        "Praça circular ao ar livre com bancos de mármore e uma fonte central. "
        "O coração do Campus onde qualquer um pode falar e ser ouvido. "
        "Debates espontâneos nascem aqui diariamente."
    ),
    tipo="publico",
    capacidade=50,
    categorias_afinidade=[
        "influencia_oratoria", "politica_brasileira",
        "politica_internacional", "estrategia",
    ],
    horario_pico=(10, 20),
    nivel_formalidade=3,
    nivel_energia=8,
    conexoes=[
        "torre_estrategia", "cafe_filosofos", "arena_debates",
        "jardim_visionarios", "refeitorio", "terraco",
    ],
    objetos=["tribuna", "fonte", "paineis_digitais", "bancos_circulares"],
    posicao_x=0.5,
    posicao_y=0.5,
))

_registrar(Local(
    id="torre_estrategia",
    nome="Torre de Estratégia",
    descricao=(
        "Edifício de vidro com 5 andares. Salas de war room com telas gigantes, "
        "mapas interativos e dashboards em tempo real. "
        "Onde decisões que mudam o jogo são tomadas."
    ),
    tipo="trabalho",
    capacidade=25,
    categorias_afinidade=[
        "estrategia", "investidor", "br_business",
        "negociacao", "politica_internacional",
    ],
    horario_pico=(8, 19),
    nivel_formalidade=8,
    nivel_energia=7,
    conexoes=["agora", "sala_guerra", "laboratorio", "auditorio"],
    objetos=[
        "mesa_estrategica", "telas_dados", "quadro_cenarios",
        "mapas_geopoliticos", "dashboard_tempo_real",
    ],
    posicao_x=0.3,
    posicao_y=0.3,
))

_registrar(Local(
    id="biblioteca",
    nome="Biblioteca Infinita",
    descricao=(
        "Três andares de estantes que parecem não ter fim. "
        "Seções por disciplina, cantos de leitura silenciosa, "
        "terminais de pesquisa com acesso a tudo já publicado. "
        "O silêncio aqui é sagrado."
    ),
    tipo="trabalho",
    capacidade=30,
    categorias_afinidade=[
        "qi_extremo", "estrategia", "ia_futuro",
        "jurista_lendario", "mindset",
    ],
    horario_pico=(7, 22),
    nivel_formalidade=7,
    nivel_energia=2,
    conexoes=["cafe_filosofos", "laboratorio", "galeria", "observatorio"],
    objetos=[
        "estantes_infinitas", "terminal_pesquisa", "mesa_estudo",
        "globo_antigo", "manuscritos_raros",
    ],
    posicao_x=0.7,
    posicao_y=0.3,
))

_registrar(Local(
    id="cafe_filosofos",
    nome="Café dos Filósofos",
    descricao=(
        "Café aconchegante com mesas redondas de madeira escura. "
        "Cheiro de café fresco e som de jazz suave. "
        "As melhores ideias nascem de conversas aqui, sem agenda."
    ),
    tipo="lazer",
    capacidade=20,
    categorias_afinidade=[
        "influencia_oratoria", "mindset", "resiliencia",
        "omega", "ficticio",
    ],
    horario_pico=(8, 21),
    nivel_formalidade=2,
    nivel_energia=5,
    conexoes=["agora", "biblioteca", "jardim_visionarios", "atelie"],
    objetos=[
        "maquina_cafe", "quadro_negro", "livros_emprestados",
        "violao_canto", "mesas_redondas",
    ],
    posicao_x=0.5,
    posicao_y=0.3,
))

_registrar(Local(
    id="arena_debates",
    nome="Arena de Debates",
    descricao=(
        "Anfiteatro semicircular com acústica perfeita. "
        "Dois púlpitos opostos, plateia elevada, placar de argumentos. "
        "Debates estruturados com regras claras e moderação."
    ),
    tipo="trabalho",
    capacidade=40,
    categorias_afinidade=[
        "influencia_oratoria", "jurista_lendario",
        "politica_brasileira", "lado_negro",
    ],
    horario_pico=(14, 20),
    nivel_formalidade=7,
    nivel_energia=9,
    conexoes=["agora", "tribunal", "auditorio"],
    objetos=[
        "pulpitos", "placar_argumentos", "relogio_debate",
        "microfones", "tela_projecao",
    ],
    posicao_x=0.3,
    posicao_y=0.7,
))

_registrar(Local(
    id="jardim_visionarios",
    nome="Jardim dos Visionários",
    descricao=(
        "Jardim paisagístico com caminhos sinuosos, bancos sob árvores, "
        "esculturas abstratas e uma vista panorâmica do horizonte. "
        "Onde ideias impossíveis se tornam possíveis."
    ),
    tipo="lazer",
    capacidade=25,
    categorias_afinidade=[
        "visionario", "tech", "ia_futuro",
        "marca", "mkt_digital",
    ],
    horario_pico=(7, 19),
    nivel_formalidade=1,
    nivel_energia=4,
    conexoes=["agora", "cafe_filosofos", "observatorio", "terraco"],
    objetos=[
        "banco_arvore", "esculturas", "fonte_meditacao",
        "caminho_labirinto", "mirante",
    ],
    posicao_x=0.7,
    posicao_y=0.5,
))

_registrar(Local(
    id="tribunal",
    nome="Tribunal da Razão",
    descricao=(
        "Sala solene com paredes de mogno, bancada elevada de juízes, "
        "mesa de defesa e acusação. Aqui se julga a validade de ideias, "
        "não pessoas. A lógica é a lei suprema."
    ),
    tipo="trabalho",
    capacidade=20,
    categorias_afinidade=[
        "jurista_lendario", "politica_brasileira",
        "influencia_oratoria", "estrategia",
    ],
    horario_pico=(9, 17),
    nivel_formalidade=10,
    nivel_energia=6,
    conexoes=["arena_debates", "biblioteca", "torre_estrategia"],
    objetos=[
        "bancada_juizes", "mesa_defesa", "mesa_acusacao",
        "codigo_leis", "balanca_justica",
    ],
    posicao_x=0.2,
    posicao_y=0.7,
))

_registrar(Local(
    id="laboratorio",
    nome="Laboratório de Ideias",
    descricao=(
        "Espaço high-tech com quadros brancos gigantes, impressoras 3D, "
        "computadores quânticos simulados e prototipagem rápida. "
        "Onde teoria vira prática."
    ),
    tipo="trabalho",
    capacidade=15,
    categorias_afinidade=[
        "tech", "ia_futuro", "qi_extremo",
        "visionario", "mkt_digital",
    ],
    horario_pico=(9, 21),
    nivel_formalidade=4,
    nivel_energia=7,
    conexoes=["torre_estrategia", "biblioteca", "observatorio"],
    objetos=[
        "quadros_brancos", "computadores", "impressora_3d",
        "prototipo_mesa", "telas_holograficas",
    ],
    posicao_x=0.5,
    posicao_y=0.2,
))

_registrar(Local(
    id="galeria",
    nome="Galeria dos Legados",
    descricao=(
        "Museu interativo com hologramas de personalidades históricas. "
        "Cada consultor falecido tem uma ala dedicada com suas obras, "
        "frases e contribuições. Inspiração em cada corredor."
    ),
    tipo="especial",
    capacidade=30,
    categorias_afinidade=[
        "resiliencia", "omega", "ficticio",
        "mindset", "influencia_oratoria",
    ],
    horario_pico=(10, 20),
    nivel_formalidade=6,
    nivel_energia=3,
    conexoes=["biblioteca", "atelie", "jardim_visionarios"],
    objetos=[
        "hologramas", "obras_arte", "paineis_interativos",
        "bustos_bronze", "linha_do_tempo",
    ],
    posicao_x=0.8,
    posicao_y=0.4,
))

_registrar(Local(
    id="sala_guerra",
    nome="Sala de Guerra",
    descricao=(
        "Bunker subterrâneo com mesas de areia digital, comunicações "
        "criptografadas e painéis de cenários. Para quando as decisões "
        "não podem esperar e os riscos são máximos."
    ),
    tipo="especial",
    capacidade=12,
    categorias_afinidade=[
        "estrategia", "negociacao", "politica_internacional",
        "lado_negro", "investidor",
    ],
    horario_pico=(8, 22),
    nivel_formalidade=9,
    nivel_energia=10,
    conexoes=["torre_estrategia", "tribunal"],
    objetos=[
        "mesa_areia_digital", "paineis_cenarios", "telefone_vermelho",
        "mapa_tatico", "relogio_contagem",
    ],
    posicao_x=0.2,
    posicao_y=0.4,
))

_registrar(Local(
    id="auditorio",
    nome="Auditório INTEIA",
    descricao=(
        "Auditório com 200 lugares, palco com tela panorâmica de 20m. "
        "Para masterclasses, keynotes e apresentações que mudam paradigmas."
    ),
    tipo="trabalho",
    capacidade=60,
    categorias_afinidade=[
        "influencia_oratoria", "visionario", "tech",
        "marca", "mindset",
    ],
    horario_pico=(14, 18),
    nivel_formalidade=8,
    nivel_energia=7,
    conexoes=["torre_estrategia", "arena_debates", "agora"],
    objetos=[
        "palco", "tela_panoramica", "microfones",
        "poltronas_vip", "bastidores",
    ],
    posicao_x=0.3,
    posicao_y=0.5,
))

_registrar(Local(
    id="atelie",
    nome="Ateliê dos Artesãos",
    descricao=(
        "Espaço luminoso com luz natural, cavaletes, instrumentos musicais "
        "e ferramentas de criação. A expressão artística como forma de pensamento."
    ),
    tipo="lazer",
    capacidade=15,
    categorias_afinidade=[
        "marca", "ficticio", "mindset",
        "resiliencia", "omega",
    ],
    horario_pico=(9, 20),
    nivel_formalidade=1,
    nivel_energia=5,
    conexoes=["cafe_filosofos", "galeria", "residencias_leste"],
    objetos=[
        "cavaletes", "instrumentos", "argila",
        "tintas", "mesa_criacao",
    ],
    posicao_x=0.8,
    posicao_y=0.6,
))

_registrar(Local(
    id="observatorio",
    nome="Observatório do Futuro",
    descricao=(
        "Cúpula de vidro no ponto mais alto do campus. "
        "Telescópios, telas com dados em tempo real do mundo, "
        "modelos preditivos. Onde se antecipa o que vem."
    ),
    tipo="especial",
    capacidade=10,
    categorias_afinidade=[
        "ia_futuro", "visionario", "qi_extremo",
        "tech", "investidor",
    ],
    horario_pico=(6, 23),
    nivel_formalidade=5,
    nivel_energia=4,
    conexoes=["jardim_visionarios", "biblioteca", "laboratorio"],
    objetos=[
        "telescopio", "telas_dados_globais", "modelos_preditivos",
        "mapa_tendencias", "cadeira_contemplacao",
    ],
    posicao_x=0.8,
    posicao_y=0.2,
))

# --- RESIDÊNCIAS ---

_registrar(Local(
    id="residencias_norte",
    nome="Residências Norte",
    descricao=(
        "Ala residencial moderna com suítes individuais. "
        "Abriga visionários, empreendedores tech e investidores."
    ),
    tipo="residencia",
    capacidade=40,
    categorias_afinidade=[
        "visionario", "tech", "investidor",
        "ia_futuro", "mkt_digital",
    ],
    horario_pico=(22, 7),
    nivel_formalidade=2,
    nivel_energia=2,
    conexoes=["laboratorio", "observatorio", "refeitorio"],
    objetos=["suites", "lounge", "kitchenette"],
    posicao_x=0.5,
    posicao_y=0.1,
))

_registrar(Local(
    id="residencias_sul",
    nome="Residências Sul",
    descricao=(
        "Ala residencial clássica com acabamento em mogno. "
        "Abriga políticos, juristas e líderes governamentais."
    ),
    tipo="residencia",
    capacidade=40,
    categorias_afinidade=[
        "politica_brasileira", "politica_internacional",
        "jurista_lendario", "negociacao",
    ],
    horario_pico=(22, 7),
    nivel_formalidade=5,
    nivel_energia=2,
    conexoes=["tribunal", "arena_debates", "refeitorio"],
    objetos=["suites", "sala_leitura", "escritorio_privado"],
    posicao_x=0.5,
    posicao_y=0.9,
))

_registrar(Local(
    id="residencias_leste",
    nome="Residências Leste",
    descricao=(
        "Ala residencial tranquila com jardim zen. "
        "Abriga filósofos, psicólogos e líderes espirituais."
    ),
    tipo="residencia",
    capacidade=30,
    categorias_afinidade=[
        "mindset", "resiliencia", "ficticio",
        "omega", "influencia_oratoria",
    ],
    horario_pico=(22, 7),
    nivel_formalidade=3,
    nivel_energia=1,
    conexoes=["atelie", "galeria", "refeitorio", "cafe_filosofos"],
    objetos=["suites", "jardim_zen", "sala_meditacao"],
    posicao_x=0.9,
    posicao_y=0.5,
))

_registrar(Local(
    id="residencias_oeste",
    nome="Residências Oeste",
    descricao=(
        "Ala residencial executiva com salas de reunião privadas. "
        "Abriga estrategistas, negociadores e executivos de marketing."
    ),
    tipo="residencia",
    capacidade=30,
    categorias_afinidade=[
        "estrategia", "negociacao", "marca",
        "br_business", "lado_negro",
    ],
    horario_pico=(22, 7),
    nivel_formalidade=6,
    nivel_energia=2,
    conexoes=["torre_estrategia", "sala_guerra", "refeitorio"],
    objetos=["suites", "sala_reuniao_privada", "bar_executivo"],
    posicao_x=0.1,
    posicao_y=0.5,
))

# --- SERVIÇOS ---

_registrar(Local(
    id="refeitorio",
    nome="Refeitório Central",
    descricao=(
        "Amplo salão de refeições com culinária internacional. "
        "Mesas de 4 a 8 pessoas incentivam encontros inesperados. "
        "Chef premiado prepara pratos que facilitam conversas."
    ),
    tipo="lazer",
    capacidade=60,
    categorias_afinidade=[],  # todos
    horario_pico=(7, 21),
    nivel_formalidade=3,
    nivel_energia=6,
    conexoes=[
        "agora", "residencias_norte", "residencias_sul",
        "residencias_leste", "residencias_oeste",
    ],
    objetos=["mesas_longas", "buffet", "bar_sucos", "tv_noticias"],
    posicao_x=0.4,
    posicao_y=0.6,
))

_registrar(Local(
    id="terraco",
    nome="Terraço Panorâmico",
    descricao=(
        "Terraço no topo do edifício central com vista 360 graus. "
        "Poltronas, jardim vertical, bar de cocktails. "
        "O local favorito para networking ao pôr do sol."
    ),
    tipo="lazer",
    capacidade=20,
    categorias_afinidade=[
        "investidor", "br_business", "marca",
        "visionario", "mkt_digital",
    ],
    horario_pico=(17, 23),
    nivel_formalidade=4,
    nivel_energia=5,
    conexoes=["agora", "jardim_visionarios", "auditorio"],
    objetos=[
        "bar_cocktails", "poltronas_panoramicas",
        "jardim_vertical", "telescopio_amador",
    ],
    posicao_x=0.6,
    posicao_y=0.6,
))


# ============================================================
# FUNÇÕES DE NAVEGAÇÃO
# ============================================================

def obter_local(local_id: str) -> Optional[Local]:
    """Retorna um local pelo ID."""
    return LOCAIS.get(local_id)


def obter_todos_locais() -> list[Local]:
    """Retorna todos os locais do campus."""
    return list(LOCAIS.values())


def obter_conexoes(local_id: str) -> list[Local]:
    """Retorna locais conectados a um dado local."""
    local = LOCAIS.get(local_id)
    if not local:
        return []
    return [LOCAIS[c] for c in local.conexoes if c in LOCAIS]


def obter_locais_por_tipo(tipo: str) -> list[Local]:
    """Retorna locais de um tipo específico."""
    return [l for l in LOCAIS.values() if l.tipo == tipo]


def calcular_distancia(local_a_id: str, local_b_id: str) -> int:
    """Calcula distância mínima (em hops) entre dois locais via BFS."""
    if local_a_id == local_b_id:
        return 0
    if local_a_id not in LOCAIS or local_b_id not in LOCAIS:
        return -1

    visitados = {local_a_id}
    fila = [(local_a_id, 0)]

    while fila:
        atual, dist = fila.pop(0)
        for vizinho_id in LOCAIS[atual].conexoes:
            if vizinho_id == local_b_id:
                return dist + 1
            if vizinho_id not in visitados and vizinho_id in LOCAIS:
                visitados.add(vizinho_id)
                fila.append((vizinho_id, dist + 1))

    return -1  # não conectado


def residencia_para_categoria(categoria: str) -> str:
    """Retorna o ID da residência mais adequada para uma categoria."""
    melhor_local = "residencias_norte"  # fallback
    melhor_score = 0

    for local in obter_locais_por_tipo("residencia"):
        if categoria in local.categorias_afinidade:
            score = 1.0
            if score > melhor_score:
                melhor_score = score
                melhor_local = local.id

    return melhor_local


def locais_abertos(hora: int) -> list[Local]:
    """Retorna locais abertos em determinada hora."""
    abertos = []
    for local in LOCAIS.values():
        if local.tipo == "residencia":
            abertos.append(local)
            continue
        inicio, fim = local.horario_pico
        # Consideramos aberto 2h antes e 2h depois do pico
        abertura = max(0, inicio - 2)
        fechamento = min(23, fim + 2)
        if abertura <= hora <= fechamento:
            abertos.append(local)
    return abertos
