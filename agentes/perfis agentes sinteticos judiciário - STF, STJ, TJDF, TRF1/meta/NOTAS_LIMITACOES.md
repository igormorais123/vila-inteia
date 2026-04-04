# Notas e Limitacoes

## Sobre "clones"
Este repositorio NAO deve gerar nem operar agentes que se apresentem como o magistrado real, nem produzir respostas assinadas como ele/ela, nem tentar enganar terceiros.

O que esta base suporta com seguranca
- Modelos de simulacao transparentes (rotulados como simulacao) que aproximem padroes de fundamentacao juridica e tendencias observaveis em votos, obras e entrevistas.
- Sintese de dados biograficos e de carreira a partir de fontes publicas.

O que NAO esta coberto
- Afirmacoes sobre atributos psicologicos clinicos (ex: diagnosticos), vida privada, familia, endereco, ou qualquer dado nao-publico.
- Inferencias "fortes" sem evidencia (ex: motivacoes internas especificas). Inferencias operacionais devem ficar em `hipoteses_para_simulacao` com indicacao de confianca e lastro.

## Cobertura atual
- STF: dados iniciais e stubs gerados.
- STJ: nomes/posse/origem via Wikipedia (lista historica) + stubs.
- TJDFT: nomes e dados institucionais (assessoria/telefones) via pagina oficial.
- TRF1: nomes e dados institucionais (gabinete/funcao) via pagina oficial (acesso indireto via proxy de leitura).
