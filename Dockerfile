FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Sistema e dependências de build
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential libpq-dev netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
  && pip install -r requirements.txt

COPY . .

# Usar entrypoint simples
RUN chmod +x /app/docker/entrypoint_simple.sh

RUN adduser --disabled-password --gecos "" appuser \
  && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint_simple.sh"]

