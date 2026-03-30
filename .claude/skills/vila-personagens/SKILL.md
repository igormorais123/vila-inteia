# Vila INTEIA — Personagens Lendarios

> Como criar, editar e testar consultores lendarios.

## Banco de Consultores

- **Arquivo**: `data/banco-consultores-lendarios.json`
- **Total**: 151 consultores
- **Atributos**: ~100 por consultor
- **Categorias**: 23 (estrategia, qi_extremo, mindset, espiritual, etc.)
- **Tiers**: S (elite), A, B, C, legado, especial

## Sistema de Prompts Profundos (engine/arquetipos.py)

6 camadas que invocam o ARQUETIPO no inconsciente coletivo:

1. **ESSENCIA** — quem e no nivel arquetipico (bio, frase, arquetipo)
2. **VOZ** — tom, ritmo, vocabulario, expressoes
3. **MENTE** — frameworks, expertise, perguntas que faz
4. **SOMBRA** — contradicoes, falhas, pontos cegos (cria profundidade)
5. **RELACOES** — mentores, rivais, tensoes
6. **REGRAS** — comportamento inviolavel (15 personagens)

## 15 Personagens com Regras Especiais

```python
from engine.arquetipos import REGRAS_ESPECIAIS
# Jesus, Diabob, Socrates, Steve Jobs, Tesla, Einstein, Sun Tzu,
# Trump, Erickson, Jung, Rui Barbosa, Maquiavel, Marco Aurelio,
# Cleopatra, Asimov
```

## Como Adicionar Novo Consultor

```python
# 1. Criar dict com campos obrigatorios
novo = {
    "id": "CL152",
    "numero_lista": 152,
    "nome": "Nome Completo",
    "nome_exibicao": "Nome",
    "titulo": "Titulo | Subtitulo",
    "categoria": "estrategia",  # uma das 23 categorias
    "tier": "S",
    "frase_chave": "Frase iconica",
    "biografia_resumida": "...",
    "estilo_comunicacao": "...",
    "tom_voz": "...",
    "nivel_agressividade": 5,  # 1-10
    "nivel_empatia": 5,
    "nivel_carisma": 5,
    "nivel_extroversao": 5,
    "areas_expertise": ["area1", "area2"],
    "frameworks_mentais": ["framework1"],
    "instrucao_comportamental": "Voce e...",
    "ativo": True,
}

# 2. Adicionar ao JSON
import json
with open("data/banco-consultores-lendarios.json", "r+", encoding="utf-8") as f:
    banco = json.load(f)
    banco.append(novo)
    f.seek(0)
    json.dump(banco, f, ensure_ascii=False, indent=2)
    f.truncate()

# 3. (Opcional) Adicionar regras especiais em engine/arquetipos.py
```

## 20 Pares Rivais (engine/gatilhos.py)

Destaques do imaginario coletivo:
- Jesus vs Diabob (luz vs trevas)
- Socrates vs Trump (verdade vs narrativa)
- Rui Barbosa vs Maquiavel (lei vs poder)
- Jung vs Freud (coletivo vs individual)
- Marco Aurelio vs Nietzsche (estoicismo vs vontade)
- Gandhi vs Trump (nao-violencia vs poder bruto)
- Einstein vs Tesla (teoria vs invencao)
- Jobs vs Da Vinci (design moderno vs renascentista)

## Testes

```bash
# Testar todos os personagens
python tests/test_personagens.py

# Resultados esperados:
# 15/15 regras especiais com consultor
# 25/25 prompts profundos OK
# 6/6 debates OK
# 9/9 reacoes OK
# 10/10 pares rivais viaveis
```

## Exemplos de Voz por Personagem

| Personagem | Estilo | Exemplo |
|------------|--------|---------|
| Jesus | Parabola | "Havia um escriba que conhecia todas as leis, mas nunca olhou nos olhos..." |
| Diabob | Provocacao | "Adoravel. A pergunta real: quem vai substituir os JUIZES?" |
| Sun Tzu | Laconico | "Conhece o terreno, vence a batalha." |
| Socrates | Pergunta | "O que e, exatamente, 'substituir'?" |
| Trump | Showman | "Ninguem, NINGUEM fecha um deal como... Believe me." |
| Erickson | Hipnotico | "E enquanto voce pensa conscientemente... seu inconsciente ja sabe..." |
| Jung | Arquetipal | "O advogado carrega o arquetipo do Juiz Interior." |
| Maquiavel | Realismo | "Quem vai CONTROLAR a IA? O poder nao esta na ferramenta." |
| Rui Barbosa | Eloquencia | "De tanto ver triunfar as nulidades... a IA nao se corrompe." |
| Marco Aurelio | Aforismo | "Isso esta sob seu controle ou nao?" |
