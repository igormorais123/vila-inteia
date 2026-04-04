# Perfis Sinteticos (Judiciario)

Este diretorio reune perfis estruturados de magistrados (STF, STJ, TJDFT e TRF1) para uso em simulacoes e pesquisas.

Importante (escopo seguro)
- Nao e produzido nem deve ser usado qualquer conteudo para se passar por uma pessoa real (impersonacao), assinar como ela, enganar terceiros, ou gerar comunicacoes que aparentem ser do magistrado.
- O objetivo aqui e modelar, de forma transparente e auditavel, padroes publicos de decisao/jurisprudencia e trajetoria profissional, para simulacao academica/estrategica.
- Campos "hipoteses_para_simulacao" sao inferencias e devem ser tratados como aproximacoes; sempre manter rotulo de simulacao.

Estrutura
- `STF/`, `STJ/`, `TJDFT/`, `TRF1/`: um arquivo JSON por pessoa.
- `meta/schema_perfil_magistrado_v1.json`: esquema do perfil.
- `meta/indice_*.json|csv`: indices gerados por script.

Geracao/atualizacao
- Script recomendado: `scripts/judiciario/gerar_perfis_iniciais.py`
- Data de referencia (neste dataset): 2026-01-30
