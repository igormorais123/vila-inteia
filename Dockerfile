FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

ENV PORT=10000

CMD python main.py live --port ${PORT} --intervalo 60 --topico "futuro da inteligencia artificial no Brasil"
