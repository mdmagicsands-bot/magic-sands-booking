#!/usr/bin/env bash
set -euo pipefail

echo "=== Magic Sands Marketing startup ==="
echo "PORT=${PORT:-unset}"
echo "RAILWAY_ENVIRONMENT=${RAILWAY_ENVIRONMENT_NAME:-local}"
echo "SITE_PROFILE=${SITE_PROFILE:-auto}"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking marketing CMS seed..."
python manage.py seed_marketing --if-empty || echo "WARN: seed_marketing skipped or failed"

echo "Starting Gunicorn on 0.0.0.0:${PORT:-8001}..."
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8001}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance
