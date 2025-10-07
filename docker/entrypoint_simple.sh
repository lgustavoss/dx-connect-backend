#!/bin/bash

set -e

# Esperar pelos serviços externos
echo "Aguardando PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL disponível"

echo "Aguardando Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis disponível"

# Aplicar migrações
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.development}
python manage.py migrate --noinput || true

# Coletar estáticos se não estiver em DEBUG
if [ "${DJANGO_DEBUG}" != "True" ] && [ "${DJANGO_DEBUG}" != "true" ]; then
  python manage.py collectstatic --noinput || true
fi

# Iniciar o servidor
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
