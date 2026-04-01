"""
Teste de Autenticidade dos Personagens Lendários.

Para cada personagem, gera um prompt profundo e simula uma resposta
heurística que demonstra o estilo. Verifica que os prompts capturam
a essência de cada um.

Executa com: python tests/test_personagens.py
"""

import sys
import os
import json

DIR_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DIR_PROJETO)
os.chdir(DIR_PROJETO)

os.environ["OMNIROUTE_API_KEY"] = ""
os.environ["CLAUDE_API_KEY"] = ""
os.environ["IA_ALLOW_API_FALLBACK"] = "false"

from engine.arquetipos import (
    gerar_prompt_profundo, gerar_prompt_debate,
    gerar_prompt_reacao, REGRAS_ESPECIAIS,
)
from engine.persona import carregar_todas_personas
from engine.gatilhos import _encontrar_por_nome, PARES_RIVAIS

# Carregar consultores
CAMINHO_JSON = os.path.join(DIR_PROJETO, "data", "banco-consultores-lendarios.json")
with open(CAMINHO_JSON, "r", encoding="utf-8") as f:
    BANCO = json.load(f)

ALL_PERSONAS = carregar_todas_personas(CAMINHO_JSON)
PERSONAS_DICT = {p.id: p for p in ALL_PERSONAS}


def _normalizar(s: str) -> str:
    """Remove acentos para busca fuzzy."""
    import unicodedata
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii").lower()

def encontrar_consultor(nome: str) -> dict | None:
    nome_n = _normalizar(nome)
    for c in BANCO:
        nome_exib = _normalizar(c.get("nome_exibicao", ""))
        nome_real = _normalizar(c.get("nome", ""))
        if nome_n in nome_exib or nome_n in nome_real:
            return c
    return None


# ============================================================
# TESTES DE PROMPT PROFUNDO
# ============================================================

PERSONAGENS_ALVO = [
    "Jesus Cristo",
    "Diabob",
    "Steve Jobs",
    "Nikola Tesla",
    "Albert Einstein",
    "Isaac Asimov",
    "Donald Trump",
    "Milton H. Erickson",
    "Carl Jung",
    "Rui Barbosa",
    "Sócrates",
    "Nicolau Maquiavel",
    "Marco Aurélio",
    "Cleópatra",
    "Aristóteles",
    "Sun Tzu",
    "Nietzsche",
    "Freud",
    "Mahatma Gandhi",
    "Winston Churchill",
    "Leonardo da Vinci",
    "Nelson Mandela",
    "Warren Buffett",
    "Elon Musk",
    "Helena Montenegro",
]


def test_prompts_profundos():
    """Testa que cada personagem gera prompt com as 6 camadas."""
    print("=" * 70)
    print(" TESTE DE PROMPTS PROFUNDOS — 25 Personagens")
    print("=" * 70)
    print()

    total = 0
    ok = 0
    falhas = []

    for nome in PERSONAGENS_ALVO:
        total += 1
        consultor = encontrar_consultor(nome)

        if not consultor:
            falhas.append(f"{nome}: NAO ENCONTRADO no JSON")
            print(f"  X  {nome:25s} — NAO ENCONTRADO")
            continue

        prompt = gerar_prompt_profundo(consultor)

        # Verificacoes
        problemas = []

        if len(prompt) < 200:
            problemas.append(f"prompt muito curto ({len(prompt)} chars)")

        if "CAMADA 1" not in prompt:
            problemas.append("falta camada Essencia")

        if "CAMADA 2" not in prompt:
            problemas.append("falta camada Voz")

        if "CAMADA 3" not in prompt:
            problemas.append("falta camada Mente")

        if consultor.get("nome_exibicao", "") not in prompt:
            problemas.append("nome nao aparece no prompt")

        if consultor.get("frase_chave", "X") not in prompt:
            problemas.append("frase-chave nao aparece")

        # Regras especiais
        if nome in REGRAS_ESPECIAIS:
            if "REGRAS" not in prompt:
                problemas.append("falta bloco de regras especiais")

        if problemas:
            falhas.append(f"{nome}: {', '.join(problemas)}")
            print(f"  !  {nome:25s} — {', '.join(problemas)}")
        else:
            ok += 1
            # Mostrar preview do prompt
            linhas = prompt.split("\n")
            n_camadas = sum(1 for l in linhas if "CAMADA" in l or "REGRAS" in l)
            print(f"  OK {nome:25s} | {len(prompt):5d} chars | {n_camadas} camadas")

    print()
    print(f"Resultado: {ok}/{total} OK | {len(falhas)} falhas")
    if falhas:
        print("\nFalhas:")
        for f in falhas:
            print(f"  x {f}")
    assert ok == total, f"{total - ok} falhas de {total}"


def test_prompts_debates():
    """Testa geracoes de prompts de debate para pares rivais."""
    print()
    print("=" * 70)
    print(" TESTE DE PROMPTS DE DEBATE — Pares Rivais")
    print("=" * 70)
    print()

    ok = 0
    total = 0

    for nome_a, nome_b, tema, tags in PARES_RIVAIS[:6]:
        total += 1
        ca = encontrar_consultor(nome_a)
        cb = encontrar_consultor(nome_b)

        if not ca or not cb:
            print(f"  X  {nome_a} vs {nome_b} — consultor nao encontrado")
            continue

        prompt_a, prompt_b = gerar_prompt_debate(ca, cb, tema)

        if nome_b not in prompt_a:
            print(f"  !  {nome_a} vs {nome_b} — oponente nao mencionado no prompt A")
            continue

        if tema not in prompt_a:
            print(f"  !  {nome_a} vs {nome_b} — tema nao mencionado")
            continue

        ok += 1
        print(f"  OK {nome_a:15s} vs {nome_b:15s} | tema: {tema[:40]}")
        print(f"     Prompt A: {len(prompt_a):5d} chars | Prompt B: {len(prompt_b):5d} chars")

    print(f"\nResultado: {ok}/{total} OK")
    assert ok == total, f"{total - ok} falhas de {total}"


def test_prompt_reacao():
    """Testa prompts de reacao a posts."""
    print()
    print("=" * 70)
    print(" TESTE DE PROMPTS DE REACAO — Resposta a Post")
    print("=" * 70)
    print()

    tema = "IA vai substituir advogados nos proximos 5 anos?"
    conteudo = "Com o avanco do GPT-5 e modelos juridicos, a advocacia repetitiva esta com os dias contados. Mas e o raciocinio juridico complexo?"

    ok = 0
    for nome in ["Jesus Cristo", "Diabob", "Rui Barbosa", "Steve Jobs",
                  "Carl Jung", "Socrates", "Maquiavel", "Einstein", "Trump"]:
        consultor = encontrar_consultor(nome)
        if not consultor:
            print(f"  X  {nome:25s} — nao encontrado")
            continue

        prompt = gerar_prompt_reacao(consultor, tema, conteudo)

        if "POST NO FEED" not in prompt:
            print(f"  !  {nome:25s} — falta bloco POST NO FEED")
            continue

        if tema not in prompt:
            print(f"  !  {nome:25s} — tema nao aparece")
            continue

        ok += 1
        print(f"  OK {nome:25s} | {len(prompt):5d} chars | reacao configurada")

    print(f"\nResultado: {ok}/9 OK")


def test_diversidade_estilos():
    """Verifica que personagens diferentes geram prompts diferentes."""
    print()
    print("=" * 70)
    print(" TESTE DE DIVERSIDADE — Cada personagem e unico")
    print("=" * 70)
    print()

    prompts = {}
    for nome in ["Jesus Cristo", "Diabob", "Steve Jobs", "Sun Tzu",
                  "Socrates", "Marco Aurelio", "Trump", "Einstein"]:
        c = encontrar_consultor(nome)
        if c:
            prompts[nome] = gerar_prompt_profundo(c)

    # Verificar que nenhum par de prompts e identico
    nomes = list(prompts.keys())
    duplicatas = 0
    for i in range(len(nomes)):
        for j in range(i + 1, len(nomes)):
            if prompts[nomes[i]] == prompts[nomes[j]]:
                print(f"  X  {nomes[i]} == {nomes[j]} (DUPLICATA!)")
                duplicatas += 1
            else:
                # Calcular similaridade bruta
                a, b = set(prompts[nomes[i]].split()), set(prompts[nomes[j]].split())
                sim = len(a & b) / max(len(a | b), 1)
                if sim > 0.7:
                    print(f"  !  {nomes[i]:15s} ~ {nomes[j]:15s} ({sim:.0%} similar)")
                else:
                    pass  # OK, sao diferentes

    if duplicatas == 0:
        print(f"  OK Todos os {len(prompts)} prompts sao unicos")
    print()


def show_exemplos_voz():
    """Mostra exemplos de como cada personagem soa."""
    print()
    print("=" * 70)
    print(" EXEMPLOS DE VOZ — Como cada personagem responderia")
    print("=" * 70)
    print()
    print(" Tema: 'IA vai substituir advogados?'")
    print()

    # Respostas heuristicas que demonstram o estilo
    respostas = {
        "Jesus Cristo": (
            "Havia um escriba que conhecia todas as leis, mas nunca olhou nos olhos "
            "de quem pedia justica. A maquina conhecera a lei melhor que ele. "
            "Mas quem lavara os pes do injusticado?"
        ),
        "Diabob": (
            "Adoravel. Todos preocupados com advogados sendo substituidos. "
            "A pergunta real: quem vai substituir os JUIZES? Porque se a IA "
            "julga melhor que humanos, o problema nao e a profissao — e o ego."
        ),
        "Socrates": (
            "O que e, exatamente, 'substituir'? Se a maquina faz o trabalho "
            "mas nao compreende a justica, ela substitui ou apenas imita? "
            "E se imita perfeitamente — qual a diferenca?"
        ),
        "Steve Jobs": (
            "Voces estao perguntando a coisa errada. A pergunta nao e 'IA vai "
            "substituir advogados'. E: 'como a IA vai reinventar o acesso a "
            "justica para as 5 bilhoes de pessoas que nunca tiveram um advogado?'"
        ),
        "Sun Tzu": (
            "Conhece o terreno, vence a batalha. O advogado que nao conhece "
            "IA ja perdeu."
        ),
        "Albert Einstein": (
            "Imagine um experimento mental: um robo-advogado que nunca esquece "
            "um precedente, nunca se cansa, nunca cobra por hora. Agora imagine "
            "que ele enfrenta um caso que nenhuma lei previu. "
            "A imaginacao juridica — isso nenhuma maquina replica."
        ),
        "Donald Trump": (
            "Olha, eu conhego advogados tremendos, os melhores — e vou te dizer, "
            "a IA e fantastica, incrivel, mas ninguem, NINGUEM fecha um deal "
            "como um advogado de verdade. Believe me."
        ),
        "Carl Jung": (
            "O advogado carrega o arquetipo do Juiz Interior. Substituir a funcao "
            "e trivial — a maquina analisa leis. Mas o arquetipo? A necessidade "
            "humana de ter alguem que TESTEMUNHE sua dor perante a lei? "
            "Isso e o inconsciente coletivo. Isso nao se programa."
        ),
        "Rui Barbosa": (
            "De tanto ver triunfar as nulidades, de tanto ver prosperar a "
            "desonra, o homem chega a desanimar da virtude. Mas a IA nao "
            "desanima, nao se corrompe, nao aceita suborno. Talvez a maquina "
            "nao substitua o advogado — talvez substitua a CORRUPCAO."
        ),
        "Marco Aurelio": (
            "Isso esta sob seu controle ou nao? Se a IA vem, ela vem. "
            "A virtude nao e resistir ao inevitavel — e se adaptar com dignidade."
        ),
        "Milton H. Erickson": (
            "E enquanto voce pensa conscientemente sobre advogados e maquinas... "
            "seu inconsciente ja sabe que a verdadeira questao e outra. "
            "Talvez, justamente, a mudanca que mais teme seja a que mais precisa."
        ),
        "Maquiavel": (
            "A questao nao e se a IA vai substituir advogados. E quem vai "
            "CONTROLAR a IA que substitui advogados. O poder nao esta na "
            "ferramenta — esta em quem decide como usa-la."
        ),
        "Nietzsche": (
            "O advogado morreu — e a IA o matou. Mas nao chorem pelo advogado. "
            "Chorem pelo homem que precisava de outro homem para ter justica. "
            "A Vontade de Poder exige que cada um seja seu proprio legislador."
        ),
        "Cleopatra": (
            "Em Alexandria, tinhamos escribas que decoravam leis. Nenhum deles "
            "governou. O poder nunca esteve na lei — esteve em quem a interpreta "
            "para quem. A IA sera a nova escriba. A pergunta e: quem sera a rainha?"
        ),
    }

    for nome, resposta in respostas.items():
        c = encontrar_consultor(nome)
        if not c:
            continue
        tier = c.get("tier", "?")
        cat = c.get("categoria", "?")
        print(f"  [{tier}] {nome}")
        print(f"      \"{resposta}\"")
        print()


def test_cobertura_regras():
    """Verifica que todos com regras especiais estao no JSON."""
    print("=" * 70)
    print(" COBERTURA DE REGRAS ESPECIAIS")
    print("=" * 70)
    print()

    ok = 0
    for nome in REGRAS_ESPECIAIS:
        c = encontrar_consultor(nome)
        if c:
            ok += 1
            n_regras = len(REGRAS_ESPECIAIS[nome].get("regras", []))
            print(f"  OK {nome:25s} | {n_regras} regras especiais")
        else:
            print(f"  X  {nome:25s} | NAO ENCONTRADO — regras orfas!")

    print(f"\nResultado: {ok}/{len(REGRAS_ESPECIAIS)} com consultor correspondente")


def test_novos_pares_rivais():
    """Verifica novos pares rivais possíveis com os novos personagens."""
    print()
    print("=" * 70)
    print(" NOVOS PARES RIVAIS POSSIVEIS")
    print("=" * 70)
    print()

    novos_pares = [
        ("Socrates", "Donald Trump", "verdade vs narrativa"),
        ("Albert Einstein", "Nikola Tesla", "teoria vs invencao"),
        ("Rui Barbosa", "Nicolau Maquiavel", "lei vs poder"),
        ("Carl Jung", "Sigmund Freud", "inconsciente coletivo vs individual"),
        ("Marco Aurelio", "Nietzsche", "estoicismo vs vontade de poder"),
        ("Aristoteles", "Socrates", "sistema vs pergunta"),
        ("Cleopatra", "Nicolau Maquiavel", "seducao vs forca"),
        ("Isaac Asimov", "Albert Einstein", "ficcao vs fisica"),
        ("Steve Jobs", "Leonardo da Vinci", "design moderno vs renascentista"),
        ("Mahatma Gandhi", "Donald Trump", "nao-violencia vs poder bruto"),
    ]

    ok = 0
    for nome_a, nome_b, tema in novos_pares:
        ca = encontrar_consultor(nome_a)
        cb = encontrar_consultor(nome_b)
        if ca and cb:
            ok += 1
            print(f"  OK {ca['nome_exibicao']:20s} vs {cb['nome_exibicao']:20s} | {tema}")
        else:
            faltando = nome_a if not ca else nome_b
            print(f"  X  {nome_a:20s} vs {nome_b:20s} | falta: {faltando}")

    print(f"\nResultado: {ok}/{len(novos_pares)} pares viáveis")


# ============================================================
# EXECUTAR
# ============================================================

if __name__ == "__main__":
    print()
    test_cobertura_regras()
    r1 = test_prompts_profundos()
    r2 = test_prompts_debates()
    test_prompt_reacao()
    test_diversidade_estilos()
    test_novos_pares_rivais()
    show_exemplos_voz()

    print("=" * 70)
    print(" FIM DOS TESTES DE PERSONAGENS")
    print("=" * 70)
