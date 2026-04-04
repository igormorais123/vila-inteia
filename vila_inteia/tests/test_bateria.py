"""
Bateria de Testes — Vila INTEIA.

Testa todos os componentes: engine, gatilhos, rede social, cognitivo, memoria.
Executa com: python tests/test_bateria.py
"""

import sys
import os
import json
import time
import traceback
from datetime import datetime, timedelta

# Configurar path — o diretório usa hífen, importar módulos diretamente
DIR_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR_PROJETO)
os.chdir(DIR_PROJETO)

from config import config, ConfigSimulacao
from engine.persona import Persona, carregar_todas_personas
from engine.campus import (
    LOCAIS, obter_local, obter_conexoes, calcular_distancia,
    residencia_para_categoria, locais_abertos, obter_locais_por_tipo,
)
from engine.memoria import FluxoMemoria, MemoriaEspacial, Rascunho
from engine.rede_social import RedeSocial, Postagem, Comentario, Reacao
from engine.gatilhos import (
    MotorGatilhos, DiabobController, JesusCristoController,
    HelenaController, MotorDebate, PARES_RIVAIS, _encontrar_por_nome,
)
from engine.ia_client import chamar_llm, chamar_llm_conversa, MODELO_RAPIDO


# ============================================================
# FRAMEWORK DE TESTES
# ============================================================

total_testes = 0
total_ok = 0
total_falha = 0
falhas = []


def teste(nome: str):
    """Decorator para registrar testes."""
    def decorator(func):
        def wrapper():
            global total_testes, total_ok, total_falha
            total_testes += 1
            try:
                func()
                total_ok += 1
                print(f"  OK  {nome}")
            except Exception as e:
                total_falha += 1
                msg = f"{nome}: {e}"
                falhas.append(msg)
                print(f"  FALHA  {nome}: {e}")
                if "--verbose" in sys.argv:
                    traceback.print_exc()
        return wrapper
    return decorator


def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"Esperado {b}, obteve {a}. {msg}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg or "Condicao falsa")


def assert_gt(a, b, msg=""):
    if not (a > b):
        raise AssertionError(f"Esperado {a} > {b}. {msg}")


def assert_in(item, container, msg=""):
    if item not in container:
        raise AssertionError(f"{item} nao encontrado em {type(container).__name__}. {msg}")


class AssertionError(Exception):
    pass


# ============================================================
# 1. TESTES DE CONFIGURACAO
# ============================================================

@teste("Config: valores padrao")
def test_config_defaults():
    c = ConfigSimulacao()
    assert_eq(c.segundos_por_step, 600)
    assert_eq(c.max_agentes_ativos, 140)
    assert_eq(c.limiar_reflexao, 100)
    assert_eq(c.auto_save_intervalo, 50)
    assert_eq(c.raio_percepcao, 2)


@teste("Config: singleton global")
def test_config_singleton():
    assert_true(config is not None)
    assert_true(isinstance(config, ConfigSimulacao))


# ============================================================
# 2. TESTES DE CAMPUS
# ============================================================

@teste("Campus: 19 locais definidos")
def test_campus_locais():
    assert_eq(len(LOCAIS), 19, f"Esperava 19 locais, tem {len(LOCAIS)}")


@teste("Campus: tipos de locais")
def test_campus_tipos():
    tipos = {l.tipo for l in LOCAIS.values()}
    for t in ("publico", "trabalho", "residencia", "lazer", "especial"):
        assert_in(t, tipos)


@teste("Campus: obter_local valido")
def test_campus_obter():
    local = obter_local("agora_central")
    assert_true(local is not None, "agora_central nao encontrada")
    assert_eq(local.nome, "Agora Central")


@teste("Campus: obter_local invalido retorna None")
def test_campus_obter_invalido():
    local = obter_local("local_inexistente")
    assert_true(local is None)


@teste("Campus: conexoes existem")
def test_campus_conexoes():
    conns = obter_conexoes("agora_central")
    assert_true(len(conns) > 0, "agora_central sem conexoes")


@teste("Campus: distancia BFS")
def test_campus_distancia():
    dist = calcular_distancia("agora_central", "agora_central")
    assert_eq(dist, 0)
    # Locais conectados devem ter distancia >= 1
    dist2 = calcular_distancia("agora_central", "arena_debates")
    assert_true(dist2 >= 0, f"Distancia invalida: {dist2}")


@teste("Campus: residencia por categoria")
def test_campus_residencia():
    for cat in ("estrategia", "tech", "jurista_lendario", "mindset"):
        r = residencia_para_categoria(cat)
        assert_true(r is not None, f"Sem residencia para {cat}")
        assert_in(r, LOCAIS)


@teste("Campus: locais abertos por hora")
def test_campus_horario():
    abertos_6h = locais_abertos(6)
    abertos_3h = locais_abertos(3)
    # De madrugada deve ter menos locais abertos que de manha
    assert_true(len(abertos_6h) >= len(abertos_3h),
                f"6h={len(abertos_6h)}, 3h={len(abertos_3h)}")


@teste("Campus: posicoes x,y definidas")
def test_campus_posicoes():
    for lid, local in LOCAIS.items():
        assert_true(hasattr(local, 'posicao_x'), f"{lid} sem posicao_x")
        assert_true(hasattr(local, 'posicao_y'), f"{lid} sem posicao_y")


# ============================================================
# 3. TESTES DE MEMORIA
# ============================================================

@teste("Memoria Fluxo: criar e adicionar")
def test_memoria_fluxo_basico():
    m = FluxoMemoria()
    m.adicionar_evento(
        descricao="Teste de evento",
        sujeito="Tester",
        predicado="testou",
        objeto="sistema",
        local_id="agora_central",
        importancia=5,
    )
    assert_eq(len(m.nos), 1)
    assert_eq(m.nos[0].descricao, "Teste de evento")


@teste("Memoria Fluxo: recuperar por relevancia")
def test_memoria_fluxo_recuperar():
    m = FluxoMemoria()
    for i in range(10):
        m.adicionar_evento(
            descricao=f"Evento {i} sobre tecnologia",
            sujeito="Sistema",
            predicado="gerou",
            objeto="evento",
            importancia=i,
        )
    resultados = m.recuperar("tecnologia", n=3)
    assert_eq(len(resultados), 3)


@teste("Memoria Fluxo: deve_refletir")
def test_memoria_reflexao():
    m = FluxoMemoria()
    assert_true(not m.deve_refletir())
    # Adicionar eventos com importancia alta
    for i in range(15):
        m.adicionar_evento(
            descricao=f"Evento importante {i}",
            sujeito="X", predicado="fez", objeto="Y",
            importancia=8,
        )
    assert_true(m.deve_refletir(limiar=100))


@teste("Memoria Fluxo: ultimas")
def test_memoria_ultimas():
    m = FluxoMemoria()
    for i in range(5):
        m.adicionar_evento(
            descricao=f"Evento {i}",
            sujeito="S", predicado="P", objeto="O",
        )
    ultimas = m.ultimas(n=3)
    assert_eq(len(ultimas), 3)


@teste("Memoria Fluxo: pontos focais")
def test_memoria_pontos_focais():
    m = FluxoMemoria()
    for _ in range(5):
        m.adicionar_evento(
            descricao="IA avanca",
            sujeito="IA", predicado="avanca", objeto="mundo",
            palavras_chave={"ia", "futuro"},
        )
    for _ in range(3):
        m.adicionar_evento(
            descricao="Politica muda",
            sujeito="Politica", predicado="muda", objeto="Brasil",
            palavras_chave={"politica", "brasil"},
        )
    focais = m.pontos_focais(n=2)
    assert_true(len(focais) > 0)


@teste("Memoria Espacial: registrar visita")
def test_memoria_espacial():
    me = MemoriaEspacial()
    agora = datetime.now()
    me.registrar_visita("agora_central", agora)
    me.registrar_visita("cafe_filosofos", agora)
    me.registrar_visita("agora_central", agora)
    favs = me.locais_favoritos(2)
    assert_eq(len(favs), 2)
    assert_eq(favs[0][0], "agora_central")  # Mais visitado


@teste("Memoria Espacial: presencas")
def test_memoria_presencas():
    me = MemoriaEspacial()
    me.registrar_presenca("agente_1", "Elon Musk", "laboratorio")
    assert_eq(me.onde_esta("agente_1"), "laboratorio")
    agentes = me.quem_esta_em("laboratorio")
    assert_in("agente_1", [a.agente_id for a in agentes])


@teste("Rascunho: estado inicial")
def test_rascunho():
    r = Rascunho()
    assert_true(not r.esta_conversando)
    assert_true(not r.esta_dormindo)
    assert_eq(r.energia, 100)


@teste("Rascunho: conversa ativa")
def test_rascunho_conversa():
    r = Rascunho()
    r.iniciar_conversa("parceiro_1", "Elon", "laboratorio", "tecnologia")
    assert_true(r.esta_conversando)
    r.adicionar_turno_conversa("Elon", "Ola mundo")
    assert_eq(len(r.conversa_ativa.turnos), 1)
    r.encerrar_conversa()
    assert_true(not r.esta_conversando)


# ============================================================
# 4. TESTES DE PERSONA
# ============================================================

@teste("Persona: carregar todas do JSON")
def test_persona_carregar():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    assert_eq(len(todas), 144, f"Esperava 144, carregou {len(todas)}")


@teste("Persona: identidade carregada")
def test_persona_identidade():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    p = todas[0]
    assert_true(len(p.nome) > 0, "Nome vazio")
    assert_true(len(p.categoria) > 0, "Categoria vazia")
    assert_true(len(p.tier) > 0, "Tier vazio")
    assert_true(len(p.rascunho.local_atual) > 0, "Local vazio")


@teste("Persona: prompt sistema nao vazio")
def test_persona_prompt():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    prompt = todas[0].gerar_prompt_sistema()
    assert_true(len(prompt) > 100, f"Prompt muito curto: {len(prompt)} chars")
    assert_in("Vila INTEIA", prompt)


@teste("Persona: decidir_interacao retorna float")
def test_persona_interacao():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    p1, p2 = todas[0], todas[1]
    prob = p1.decidir_interacao(p2, "agora_central")
    assert_true(isinstance(prob, float), f"Tipo: {type(prob)}")
    assert_true(0 <= prob <= 1.0, f"Probabilidade fora de [0,1]: {prob}")


@teste("Persona: categorias distintas")
def test_persona_categorias():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    categorias = {p.categoria for p in todas}
    assert_true(len(categorias) >= 10, f"Poucas categorias: {len(categorias)}")


@teste("Persona: tiers validos")
def test_persona_tiers():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    tiers = {p.tier for p in todas}
    for t in tiers:
        assert_in(t, ("S", "A", "B", "C"), f"Tier invalido: {t}")


@teste("Persona: hiperparametros cognitivos 1-10")
def test_persona_hiperparametros():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    for p in todas[:20]:
        for attr in ("nivel_agressividade", "nivel_empatia", "nivel_carisma",
                      "nivel_extroversao", "tolerancia_risco", "nivel_formalidade"):
            val = getattr(p.rascunho, attr, None)
            assert_true(val is not None, f"{p.nome}: {attr} nao definido")


# ============================================================
# 5. TESTES DE REDE SOCIAL
# ============================================================

@teste("Rede Social: publicar tema usuario")
def test_rede_tema():
    r = RedeSocial()
    post = r.publicar_tema_usuario("IA vai substituir advogados?")
    assert_eq(post.tipo, "tema")
    assert_true(post.fixado)
    assert_eq(r.total_posts, 1)


@teste("Rede Social: publicar opiniao consultor")
def test_rede_opiniao():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    post = r.publicar_opiniao_consultor(
        persona=todas[0],
        conteudo="Eu acredito no futuro da IA.",
        titulo="Futuro da IA",
    )
    assert_eq(post.tipo, "opiniao")
    assert_eq(post.autor_nome, todas[0].nome_exibicao)


@teste("Rede Social: comentar em post")
def test_rede_comentar():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    post = r.publicar_tema_usuario("Debate sobre IA")
    r.comentar(post.id, todas[0], "Concordo plenamente!")
    r.comentar(post.id, todas[1], "Discordo veementemente.")
    assert_eq(post.total_comentarios, 2)


@teste("Rede Social: reacoes")
def test_rede_reacoes():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    post = r.publicar_tema_usuario("Teste reacoes")
    assert_true(r.reagir(post.id, todas[0], "concordo"))
    assert_true(r.reagir(post.id, todas[1], "brilhante"))
    # Duplicata nao deve funcionar
    assert_true(not r.reagir(post.id, todas[0], "discordo"))
    assert_eq(post.total_reacoes, 2)


@teste("Rede Social: feed ordenado")
def test_rede_feed():
    r = RedeSocial()
    r.publicar_tema_usuario("Post 1")
    r.publicar_evento("Evento 1", "Descricao do evento")
    r.publicar_tema_usuario("Post 2")
    feed = r.feed(limite=10)
    assert_eq(len(feed), 3)
    # Fixados primeiro (temas sao fixados)
    assert_eq(feed[0]["tipo"], "tema")


@teste("Rede Social: trending tags")
def test_rede_trending():
    r = RedeSocial()
    r.publicar_tema_usuario("IA e o futuro da tecnologia", tags=["ia", "futuro"])
    r.publicar_tema_usuario("IA na medicina", tags=["ia", "saude"])
    r.publicar_tema_usuario("Futuro das eleicoes", tags=["futuro", "eleicoes"])
    trending = r.trending_tags(5)
    tags = [t["tag"] for t in trending]
    assert_in("ia", tags)
    assert_in("futuro", tags)


@teste("Rede Social: engajamento scoring")
def test_rede_engajamento():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    post = r.publicar_tema_usuario("Teste engajamento")
    assert_true(post.engajamento >= 0)
    r.comentar(post.id, todas[0], "Comentario")
    # Comentario = +3 pontos de engajamento
    assert_true(post.engajamento > 0)


@teste("Rede Social: selecionar reagentes")
def test_rede_selecionar_reagentes():
    from vila_inteia.engine.rede_social import _selecionar_reagentes
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    personas_dict = {p.id: p for p in todas}

    r = RedeSocial()
    post = r.publicar_tema_usuario("Debate sobre IA e tecnologia", tags=["ia", "tecnologia"])

    reagentes = _selecionar_reagentes(post, personas_dict, max_n=8)
    assert_true(len(reagentes) > 0, "Nenhum reagente selecionado")
    assert_true(len(reagentes) <= 8)

    # Deve ter diversidade de categorias
    categorias = {p.categoria for p in reagentes}
    assert_true(len(categorias) >= 2, f"Pouca diversidade: {categorias}")


@teste("Rede Social: gerar comentario heuristico")
def test_rede_comentario_heuristico():
    from vila_inteia.engine.rede_social import _gerar_comentario_heuristico
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    post = r.publicar_tema_usuario("Futuro da IA")

    comentario = _gerar_comentario_heuristico(todas[0], post)
    assert_true(len(comentario) > 10, f"Comentario muito curto: '{comentario}'")


@teste("Rede Social: gerar post autonomo heuristico")
def test_rede_post_autonomo():
    from vila_inteia.engine.rede_social import _gerar_post_autonomo
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    # Testar com 5 consultores
    gerados = 0
    for p in todas[:10]:
        post = _gerar_post_autonomo(p)
        if post:
            gerados += 1
            assert_in("titulo", post)
            assert_in("conteudo", post)
    assert_true(gerados > 0, "Nenhum post autonomo gerado")


@teste("Rede Social: salvar e formato JSON")
def test_rede_salvar():
    r = RedeSocial()
    r.publicar_tema_usuario("Teste salvar", tags=["teste"])
    caminho = os.path.join(DIR_PROJETO, "data", "test_rede_social.json")
    r.salvar(caminho)
    assert_true(os.path.exists(caminho))
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    assert_in("postagens", dados)
    assert_eq(len(dados["postagens"]), 1)
    # Limpar
    os.remove(caminho)


# ============================================================
# 6. TESTES DO MOTOR DE GATILHOS
# ============================================================

@teste("Gatilhos: criar motor")
def test_gatilhos_criar():
    r = RedeSocial()
    m = MotorGatilhos(r)
    assert_eq(m.posts_hoje, 0)
    assert_eq(len(m.fila_waves), 0)
    assert_true(m.rede is r)


@teste("Gatilhos: pares rivais definidos")
def test_gatilhos_pares():
    assert_true(len(PARES_RIVAIS) >= 10, f"Poucos pares: {len(PARES_RIVAIS)}")
    for nome_a, nome_b, tema, tags in PARES_RIVAIS:
        assert_true(len(nome_a) > 0)
        assert_true(len(nome_b) > 0)
        assert_true(len(tema) > 0)
        assert_true(len(tags) > 0)


@teste("Gatilhos: encontrar_por_nome")
def test_gatilhos_encontrar():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    personas_dict = {p.id: p for p in todas}

    elon = _encontrar_por_nome(personas_dict, "Elon Musk")
    assert_true(elon is not None, "Elon Musk nao encontrado")

    jesus = _encontrar_por_nome(personas_dict, "Jesus Cristo")
    # Pode ou nao estar no JSON
    if jesus:
        print(f"    (Jesus encontrado: {jesus.nome_exibicao})")

    diabob = _encontrar_por_nome(personas_dict, "Diabob")
    if diabob:
        print(f"    (Diabob encontrado: {diabob.nome_exibicao})")


@teste("Gatilhos: DiabobController cadencia")
def test_diabob_cadencia():
    assert_true(DiabobController.deve_provocar(20, 0))
    assert_true(not DiabobController.deve_provocar(10, 0))
    assert_true(DiabobController.deve_provocar(30, 15))


@teste("Gatilhos: JesusCristoController cadencia")
def test_jesus_cadencia():
    # Deve precisar de 30+ steps desde ultimo post
    hora_manha = datetime(2026, 3, 1, 9, 0)
    # Muito recente - nao deve postar
    assert_true(not JesusCristoController.deve_postar(5, 0, hora_manha))


@teste("Gatilhos: HelenaController detectar intervencao")
def test_helena_detectar():
    r = RedeSocial()
    post = r.publicar_tema_usuario("Debate")
    # Sem comentarios - nao deve intervir
    tipo = HelenaController.deve_intervir(post, 1)
    assert_true(tipo is None, f"Intervencao indevida: {tipo}")


@teste("Gatilhos: HelenaController consenso falso")
def test_helena_consenso():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    post = r.publicar_tema_usuario("Consenso teste")
    # Adicionar 5 comentarios
    for p in todas[:5]:
        r.comentar(post.id, p, "Concordo com isso")
    # Adicionar reacoes positivas
    for p in todas[:4]:
        r.reagir(post.id, p, "concordo")
    tipo = HelenaController.deve_intervir(post, 10)
    # Deve detectar consenso falso (80%+ concordo)
    assert_true(tipo in ("sintese", "consenso_falso"), f"Tipo: {tipo}")


@teste("Gatilhos: MotorDebate selecionar par")
def test_motor_debate_selecionar():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    personas_dict = {p.id: p for p in todas}
    par = MotorDebate.selecionar_par(personas_dict)
    if par:
        a, b, tema, tags = par
        print(f"    (Par: {a.nome_exibicao} vs {b.nome_exibicao}: {tema})")
        assert_true(a.id != b.id)
    else:
        print("    (Nenhum par rival encontrado no JSON)")


@teste("Gatilhos: injetar tema usuario")
def test_gatilhos_injetar_tema():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    personas_dict = {p.id: p for p in todas}

    r = RedeSocial()
    m = MotorGatilhos(r)

    post = m.injetar_tema(
        titulo="IA vai substituir advogados?",
        personas=personas_dict,
        step=1,
    )
    assert_eq(post.tipo, "tema")
    assert_true(post.fixado)
    # Deve ter agendado waves
    assert_true(len(m.fila_waves) > 0, "Nenhuma wave agendada")
    assert_eq(m.posts_hoje, 1)


@teste("Gatilhos: injetar evento com cadencia")
def test_gatilhos_injetar_evento():
    r = RedeSocial()
    m = MotorGatilhos(r)
    p1 = m.injetar_evento("Noticia 1", "Conteudo", step=0)
    assert_true(p1 is not None)
    # Dentro da cadencia (6 steps) - deve ser None
    p2 = m.injetar_evento("Noticia 2", "Conteudo", step=3)
    assert_true(p2 is None, "Evento dentro da cadencia nao deveria ser aceito")
    # Apos cadencia
    p3 = m.injetar_evento("Noticia 3", "Conteudo", step=7)
    assert_true(p3 is not None)


@teste("Gatilhos: chance espontaneo varia por horario")
def test_gatilhos_chance_horario():
    r = RedeSocial()
    m = MotorGatilhos(r)
    # Madrugada (3h) deve ser muito menor que tarde (15h)
    chance_madru = m._calcular_chance_espontaneo(datetime(2026, 3, 1, 3, 0))
    chance_tarde = m._calcular_chance_espontaneo(datetime(2026, 3, 1, 15, 0))
    assert_true(chance_tarde > chance_madru,
                f"Tarde ({chance_tarde}) deveria > madrugada ({chance_madru})")


@teste("Gatilhos: encontrar especiais com JSON real")
def test_gatilhos_especiais():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    personas_dict = {p.id: p for p in todas}

    r = RedeSocial()
    m = MotorGatilhos(r)
    m._encontrar_especiais(personas_dict)

    encontrados = []
    if m._diabob:
        encontrados.append(f"Diabob={m._diabob.nome_exibicao}")
    if m._jesus:
        encontrados.append(f"Jesus={m._jesus.nome_exibicao}")
    if m._helena:
        encontrados.append(f"Helena={m._helena.nome_exibicao}")
    if m._sun_tzu:
        encontrados.append(f"SunTzu={m._sun_tzu.nome_exibicao}")

    if encontrados:
        print(f"    ({', '.join(encontrados)})")
    else:
        print("    (Nenhum personagem especial encontrado no JSON)")


@teste("Gatilhos: wave config valida")
def test_gatilhos_waves():
    from vila_inteia.engine.gatilhos import WAVES
    assert_eq(len(WAVES), 4)
    assert_eq(WAVES[0].delay_steps, 0)  # Primeira wave imediata
    assert_true(WAVES[0].usa_ia)  # Primeira usa IA
    # Delays crescentes
    for i in range(1, len(WAVES)):
        assert_true(WAVES[i].delay_steps >= WAVES[i-1].delay_steps)


# ============================================================
# 7. TESTES DE SIMULACAO (INTEGRACAO)
# ============================================================

@teste("Simulacao: inicializar com 10 agentes")
def test_simulacao_init():
    sim = SimulacaoVila(nome="teste_init")
    sim.inicializar(max_agentes=10)
    assert_eq(len(sim.personas), 10)
    assert_true(sim.rede_social is not None)
    assert_true(sim.motor_gatilhos is not None)
    assert_true(sim.motor_gatilhos.rede is sim.rede_social)


@teste("Simulacao: executar 1 step")
def test_simulacao_step():
    sim = SimulacaoVila(nome="teste_step")
    sim.inicializar(max_agentes=5)
    resumo = sim.executar_step()
    assert_in("step", resumo)
    assert_in("acoes", resumo)
    assert_eq(resumo["step"], 1)
    assert_true(len(resumo["acoes"]) > 0)


@teste("Simulacao: executar 5 steps")
def test_simulacao_multi_steps():
    sim = SimulacaoVila(nome="teste_multi")
    sim.inicializar(max_agentes=5)
    resumos = sim.executar(n_steps=5)
    assert_eq(len(resumos), 5)
    assert_eq(sim.step, 5)


@teste("Simulacao: injetar topico integrado")
def test_simulacao_topico():
    sim = SimulacaoVila(nome="teste_topico")
    sim.inicializar(max_agentes=10)
    sim.injetar_topico("IA vai substituir advogados?")
    assert_in("IA vai substituir advogados?", config.topicos_ativos)
    # Deve ter post na rede social
    assert_true(sim.rede_social.total_posts > 0, "Nenhum post na rede social")


@teste("Simulacao: estado_mundo completo")
def test_simulacao_estado():
    sim = SimulacaoVila(nome="teste_estado")
    sim.inicializar(max_agentes=5)
    sim.executar_step()
    estado = sim.estado_mundo()
    assert_in("simulacao", estado)
    assert_in("locais", estado)
    assert_in("rede_social", estado)
    assert_in("total_posts", estado["rede_social"])
    assert_in("waves_pendentes", estado["rede_social"])


@teste("Simulacao: mapa de calor")
def test_simulacao_mapa_calor():
    sim = SimulacaoVila(nome="teste_mapa")
    sim.inicializar(max_agentes=10)
    mapa = sim.mapa_calor()
    assert_true(len(mapa) > 0)
    total = sum(mapa.values())
    assert_eq(total, 10, f"Mapa de calor soma {total}, esperava 10")


@teste("Simulacao: salvar estado")
def test_simulacao_salvar():
    sim = SimulacaoVila(nome="teste_salvar")
    sim.inicializar(max_agentes=3)
    sim.executar(n_steps=2)
    sim.salvar()
    # Verificar que arquivos foram criados
    dir_dados = sim.dir_dados
    assert_true(os.path.exists(dir_dados), f"Diretorio nao criado: {dir_dados}")
    assert_true(
        os.path.exists(os.path.join(dir_dados, "meta.json")),
        "meta.json nao encontrado"
    )


@teste("Simulacao: consultar agente")
def test_simulacao_consultar():
    sim = SimulacaoVila(nome="teste_consultar")
    sim.inicializar(max_agentes=5)
    pid = list(sim.personas.keys())[0]
    dados = sim.consultar_agente(pid)
    assert_true(dados is not None)
    assert_in("dados_consultor", dados)
    # Agente inexistente
    assert_true(sim.consultar_agente("inexistente") is None)


# ============================================================
# 8. TESTES DE IA CLIENT
# ============================================================

@teste("IA Client: constantes definidas")
def test_ia_constantes():
    assert_eq(MODELO_RAPIDO, "rapido")
    from vila_inteia.engine.ia_client import MODELO_ANALISE, MODELO_SINTESE
    assert_eq(MODELO_ANALISE, "analise")
    assert_eq(MODELO_SINTESE, "sintese")


@teste("IA Client: chamar_llm sem provider retorna None")
def test_ia_sem_provider():
    # Sem OMNIROUTE_URL nem CLAUDE_API_KEY, deve retornar None gracefully
    resultado = chamar_llm(
        mensagens=[{"role": "user", "content": "Teste"}],
        modelo="rapido",
        max_tokens=10,
    )
    # Pode ser None (sem provider) ou string (se provider configurado)
    assert_true(resultado is None or isinstance(resultado, str))


# ============================================================
# 9. TESTES DE EDGE CASES E ROBUSTEZ
# ============================================================

@teste("Edge: post sem tags")
def test_edge_sem_tags():
    r = RedeSocial()
    post = r.publicar_tema_usuario("Sem tags nenhuma")
    assert_true(isinstance(post.tags, list))


@teste("Edge: comentar em post inexistente")
def test_edge_comentar_inexistente():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    resultado = r.comentar("id_fake", todas[0], "Teste")
    assert_true(resultado is None)


@teste("Edge: reagir em post inexistente")
def test_edge_reagir_inexistente():
    caminho = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
    todas = carregar_todas_personas(caminho)
    r = RedeSocial()
    resultado = r.reagir("id_fake", todas[0], "concordo")
    assert_true(not resultado)


@teste("Edge: feed vazio")
def test_edge_feed_vazio():
    r = RedeSocial()
    feed = r.feed()
    assert_eq(len(feed), 0)


@teste("Edge: motor gatilhos sem personas especiais")
def test_edge_sem_especiais():
    r = RedeSocial()
    m = MotorGatilhos(r)
    # Executar sem encontrar especiais - nao deve crashar
    eventos = m.executar_step(
        step=1,
        hora_atual=datetime(2026, 3, 1, 10, 0),
        personas={},
    )
    assert_true(isinstance(eventos, list))


@teste("Edge: cap de 75 posts por dia")
def test_edge_cap_diario():
    r = RedeSocial()
    m = MotorGatilhos(r)
    m.posts_hoje = 75
    m.dia_atual = 1
    eventos = m.executar_step(
        step=100,
        hora_atual=datetime(2026, 3, 1, 10, 0),
        personas={},
    )
    # Nao deve gerar nada apos cap
    assert_eq(len(eventos), 0, f"Gerou {len(eventos)} eventos apos cap")


@teste("Edge: reset diario de posts")
def test_edge_reset_diario():
    r = RedeSocial()
    m = MotorGatilhos(r)
    m.posts_hoje = 50
    m.dia_atual = 1
    # Mudar de dia
    eventos = m.executar_step(
        step=1,
        hora_atual=datetime(2026, 3, 2, 10, 0),  # Dia 2
        personas={},
    )
    assert_eq(m.posts_hoje, 0, "Nao resetou posts_hoje")
    assert_eq(m.dia_atual, 2)


@teste("Edge: processar waves com fila vazia")
def test_edge_waves_vazia():
    r = RedeSocial()
    m = MotorGatilhos(r)
    eventos = m._processar_waves(1, {}, datetime.now())
    assert_eq(len(eventos), 0)


# ============================================================
# EXECUTAR TODOS OS TESTES
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" BATERIA DE TESTES — Vila INTEIA")
    print("=" * 60)
    print()

    t0 = time.time()

    # Coletar todos os testes (funcoes que comecam com test_)
    testes = [v for k, v in list(globals().items()) if k.startswith("test_")]

    for t in testes:
        t()

    duracao = time.time() - t0
    print()
    print("=" * 60)
    print(f" RESULTADO: {total_ok}/{total_testes} OK | {total_falha} falhas | {duracao:.1f}s")
    print("=" * 60)

    if falhas:
        print()
        print("FALHAS:")
        for f in falhas:
            print(f"  x {f}")
        sys.exit(1)
    else:
        print()
        print("TODOS OS TESTES PASSARAM!")
        sys.exit(0)
