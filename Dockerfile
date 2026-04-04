FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir     fastapi>=0.109.0     'uvicorn[standard]>=0.27.0'     pydantic>=2.5.0     httpx>=0.26.0     pandas>=2.2.0     numpy>=1.26.0     scipy>=1.12.0     scikit-learn>=1.4.0     matplotlib>=3.8.0     seaborn>=0.13.0     statsmodels>=0.14.0     networkx>=3.2.0     tiktoken>=0.5.0     sse-starlette>=1.8.0     openai>=1.10.0

COPY vila_inteia/ /app/vila_inteia/
COPY agentes/ /app/data/agentes/
COPY HELENA_STRATEGOS_COMPLETA.md /app/data/
COPY AGENTES_SINTETICOS.md /app/data/

RUN mkdir -p /app/vila_inteia/data &&     ln -sf /app/data/agentes/banco-consultores-lendarios.json /app/vila_inteia/data/banco-consultores-lendarios.json &&     ln -sf /app/data/agentes/banco-consultores-lendarios.json /app/data/banco-consultores-lendarios.json && cp /app/data/agentes/banco-consultores-lendarios.json /app/vila_inteia/frontend/banco-consultores-lendarios.json

EXPOSE 8090

CMD ["uvicorn", "vila_inteia.serve:app", "--host", "0.0.0.0", "--port", "8090"]
