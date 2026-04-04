<!-- Triggers: /criar-tecnica, /nova-tecnica-ps, /skill-factory, /gerar-skill-ps -->

# Skill Factory — Geradora de Skills de Problem Solving

> Cria novas skills de resolução de problemas a partir de qualquer framework metodológico. Gera o código Python para o engine, o endpoint API, e a documentação da skill automaticamente.

## Quando Ativar

- Usuário quer adicionar uma técnica nova ao cardápio
- Encontrou um framework em livro/artigo e quer operacionalizar na Vila
- Quer adaptar uma técnica existente para contexto específico

## Como Funciona

### Input necessário

1. **Nome da técnica** (português e inglês)
2. **Fase** do ciclo: definicao | diagnostico | solucao | intervencao | avaliacao | transversal
3. **Descrição** em 1 frase
4. **Prompt estruturado** — o template de instrução para os consultores
5. **Categorias preferenciais** — quais tipos de consultor são mais relevantes
6. **Referência** — autor, ano, livro/artigo de origem

### Output gerado

1. **Função Python** no formato do `problem_solving.py`
2. **Slug** para o endpoint API
3. **Entrada no catálogo** de técnicas
4. **Teste automatizado** via curl

### Template de nova técnica

```python
@registrar("{fase}", "{slug}", "{nome}",
    "{descricao}",
    {categorias})
def {slug}(simulacao, tema: str, n: int = 5) -> dict:
    agentes = _selecionar_agentes(simulacao, n, TECNICAS["{slug}"]["categorias_pref"])
    prompt = (
        f"Aplique {nome} para: {{tema}}\n\n"
        "{prompt_estruturado}"
    )
    contribuicoes = _consultar_agentes(agentes, _SYS, prompt)
    return {{"contribuicoes": contribuicoes, "sintese": _sintetizar(contribuicoes, tema, "{nome}")}}
```

### Procedimento

1. Ler o framework/técnica fornecido pelo usuário
2. Identificar: fases, passos, outputs esperados, critérios de qualidade
3. Traduzir em prompt estruturado com formato de resposta claro
4. Gerar o código Python usando o template acima
5. Append ao arquivo `C:/Users/IgorPC/Vila-INTEIA/vila_inteia/engine/problem_solving.py`
6. Deploy: `scp` para servidor + `docker compose up -d --build`
7. Testar via curl no endpoint `/problem-solving`
8. Reportar score e métricas

### Arquivo de destino

```
C:/Users/IgorPC/Vila-INTEIA/vila_inteia/engine/problem_solving.py
```

Append a nova técnica no final do arquivo, antes do último bloco de comentário, usando o decorator `@registrar()`.

### Validação automática pós-criação

```bash
# Testar que a técnica funciona
curl -s -X POST http://72.62.108.24:8088/api/v1/vila/problem-solving \
  -H "Content-Type: application/json" \
  -d '{"tecnica": "NOVO_SLUG", "tema": "teste de validação", "n_consultores": 3}'
```

Critérios de aceite:
- Status 200
- `metricas.score_qualidade >= 8.0`
- `metricas.completude >= 0.8`
- `sintese` com mais de 200 caracteres
