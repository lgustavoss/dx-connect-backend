#!/usr/bin/env sh

set -e

# Se não existir manage.py, sobe um servidor HTTP simples para placeholder
if [ ! -f manage.py ]; then
  echo "Django não encontrado (manage.py). Iniciando placeholder em 0.0.0.0:8000..."
  exec python -m http.server 8000 --bind 0.0.0.0
fi

# Aplicar migrações automaticamente em dev
python manage.py migrate --noinput || true

# Coletar estáticos (se existir)
python manage.py collectstatic --noinput || true

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

