# CONTRIBUTING — Vila INTEIA

## Princípios

1. **Português do Brasil** em comentários, docstrings, commits, PRs e docs
2. **Sem segredos no repo**. Nunca commite `.env`, chaves API, URLs privadas, paths absolutos
3. **Tudo passa por env var**. Se precisou de valor fixo, eleve para `.env.example`
4. **Testar antes de commitar**. Mínimo: `python main.py demo` roda sem exceção
5. **Commits pequenos e coesos**. Um feature = vários commits temáticos

## Fluxo de trabalho

```bash
git checkout -b feat/nome-do-feature
# trabalha
python main.py demo                 # smoke test
git add <arquivos-específicos>      # nunca git add -A
git commit -m "feat(jornal): Chateaubriand detecta colunistas fixos"
git push -u origin feat/nome-do-feature
# abre PR contra main
```

## Padrão de nomenclatura

### Python
```python
# Funções e variáveis: snake_case em português quando domínio
def avaliar_materia(materia: MateriaBruta) -> ParecerChateaubriand: ...
def calcular_saldo(agente_id: str) -> float: ...

# Classes: PascalCase, substantivos em português
class SimulacaoVila: ...
class Persona: ...

# Constantes: UPPER_SNAKE_CASE
CATEGORIAS_VALIDAS = [...]
```

### Endpoints
```
GET  /api/v1/vila/instancias
POST /api/v1/vila/instancias
POST /api/v1/vila/instancias/{id}/pausar
GET  /api/v1/vila/constituicao/artigos
POST /api/v1/vila/constituicao/artigos/{id}/votar
```

### Commits

Prefixos aceitos:
- `feat(X)` — nova capacidade
- `fix(X)` — bugfix
- `refactor(X)` — sem mudança de comportamento
- `docs(X)` — documentação
- `chore(X)` — infra, deps, build
- `content(mirante)` — **apenas** para matérias publicadas pela Vila

Ex: `feat(chateaubriand): reescreve matérias preservando voz do autor`

## Checklist antes do PR

- [ ] `python main.py demo` roda sem exceção
- [ ] `.env` não foi alterado
- [ ] Nenhuma chave/credencial foi commitada
- [ ] Novas env vars documentadas em `.env.example`
- [ ] Se alterou schema Supabase, tem migration SQL em `sql/migrations/`
- [ ] Se criou módulo novo, tem docstring com propósito + exemplo
- [ ] README ou `docs/ARCHITECTURE.md` atualizado se for feature grande

## Testar integração com Mirante

Sem subir Mirante real:
```bash
# Modo fallback local: escreve MDX em pasta local em vez de POST
export MIRANTE_CONTENT_DIR=/tmp/mirante-test
unset MIRANTE_API_URL
python -c "
from engine.chateaubriand import escrever_materia_propria, processar_e_publicar
m = escrever_materia_propria('teste de integração', vila_id='')
print(processar_e_publicar(m))
"
ls /tmp/mirante-test/
```

## Tickets executivos

Se a Vila promulgar um artigo estrutural, aparece ticket em
`vila_tickets_executivo`. Trate como feature request vindo do sistema —
avalia, implementa se fizer sentido, responde com link do PR.

```sql
SELECT id, titulo, descricao, urgencia
FROM vila_tickets_executivo
WHERE status = 'aberto';
```
