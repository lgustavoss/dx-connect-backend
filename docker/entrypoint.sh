#!/usr/bin/env sh

set -e

# Se n??o existir manage.py, sobe um servidor HTTP simples para placeholder
if [ ! -f manage.py ]; then
  echo "Django n??o encontrado (manage.py). Iniciando placeholder em 0.0.0.0:8000..."
  exec python -m http.server 8000 --bind 0.0.0.0
fi

# Esperar pelos servi??os externos (Postgres e Redis)
POSTGRES_HOST=${POSTGRES_HOST:-db}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

python - <<PYCODE
import os, socket, time

def wait(host: str, port: int, name: str, timeout: float = 1.5, retries: int = 60):
    for attempt in range(1, retries + 1):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                print(f"{name} dispon??vel em {host}:{port}")
                return
        except OSError:
            print(f"Aguardando {name} em {host}:{port} (tentativa {attempt}/{retries})...")
            time.sleep(1)
    raise SystemExit(f"Timeout aguardando {name} em {host}:{port}")

wait(os.getenv("POSTGRES_HOST", "db"), int(os.getenv("POSTGRES_PORT", "5432")), "PostgreSQL")
wait(os.getenv("REDIS_HOST", "redis"), int(os.getenv("REDIS_PORT", "6379")), "Redis")
PYCODE

# Aplicar migra????es automaticamente em dev
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.development}

python manage.py migrate --noinput || true

# Coletar est??ticos somente quando n??o estiver em DEBUG
if [ "${DJANGO_DEBUG}" != "True" ] && [ "${DJANGO_DEBUG}" != "true" ]; then
  python manage.py collectstatic --noinput || true
fi

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

