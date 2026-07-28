#!/usr/bin/env bash
set -euo pipefail

echo "=== Magic Sands Booking startup ==="
echo "PORT=${PORT:-unset}"
echo "RAILWAY_ENVIRONMENT=${RAILWAY_ENVIRONMENT_NAME:-local}"
echo "SITE_PROFILE=${SITE_PROFILE:-auto}"

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking marketing CMS seed..."
python - <<'PY'
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from django.core.management import call_command
from marketing.models import MarketingSettings

if MarketingSettings.objects.exists():
    print("Marketing CMS already present — skipping seed_marketing.")
else:
    print("No marketing CMS rows — running seed_marketing...")
    call_command("seed_marketing")
PY

echo "Starting Gunicorn on 0.0.0.0:${PORT:-8001}..."
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8001}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  --capture-output \
  --enable-stdio-inheritance
