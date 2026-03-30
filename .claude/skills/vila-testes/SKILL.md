# Vila INTEIA — Testes

> Como rodar, criar e interpretar testes.

## Baterias de Testes

### test_bateria.py — 69 testes (0.3s)

```bash
python tests/test_bateria.py
```

| Categoria | N | O que testa |
|-----------|---|-------------|
| Config | 2 | Valores padrao, singleton |
| Campus | 7 | 19 locais, conexoes, BFS, horarios, posicoes |
| Memoria | 8 | Fluxo (eventos, recuperacao), espacial, rascunho |
| Persona | 7 | Carregar 151, identidade, prompt, interacao, tiers |
| Rede Social | 10 | Posts, comentarios, reacoes, feed, trending, heuristicos |
| Gatilhos | 12 | Motor, pares rivais, cadencia, waves, especiais |
| Simulacao | 8 | Init, steps, topico, estado, mapa calor, salvar |
| IA Client | 2 | Constantes, sem provider |
| Edge Cases | 8 | Posts vazios, IDs falsos, cap diario, reset |

### test_personagens.py — 25 personagens

```bash
python tests/test_personagens.py
```

| Teste | N | O que verifica |
|-------|---|----------------|
| Cobertura regras | 15 | Todos com regras tem consultor |
| Prompts profundos | 25 | 4-7 camadas, frase-chave, nome |
| Debates | 6 | Prompts de debate corretos |
| Reacoes | 9 | Prompts de reacao a posts |
| Diversidade | 8 | Prompts sao unicos entre si |
| Pares rivais | 10 | Novos pares viaveis |
| Exemplos de voz | 14 | Output demonstrativo |

## Como Criar Novo Teste

```python
@teste("Descricao do teste")
def test_novo():
    # Setup
    r = RedeSocial()
    # Acao
    post = r.publicar_tema_usuario("Teste")
    # Verificacao
    assert_eq(post.tipo, "tema")
    assert_true(post.fixado)
```

## Regras dos Testes

1. **Sem OmniRoute**: testes desabilitam LLM (env vars vazias)
2. **Heuristicos**: sistema funciona 100% sem LLM
3. **Imports**: usar `from engine.X import Y` (nao vila_inteia.engine)
4. **Especiais**: com max_agentes limitado, pode ter mais que o pedido (especiais extras)
