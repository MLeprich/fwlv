#!/bin/bash
# =============================================================================
# FLVS - Docker Entrypoint Script
# =============================================================================

set -e

echo "=========================================="
echo "FLVS - Feuerwehr Lagerverwaltungssystem"
echo "=========================================="

# Wait for database
echo "Waiting for database..."
while ! python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
    sleep 1
done
echo "Database is ready!"

# Wait for Redis
echo "Waiting for Redis..."
while ! python -c "import redis; redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
    sleep 1
done
echo "Redis is ready!"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if not exists (optional - controlled by env var)
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Checking for superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='${SUPERUSER_USERNAME:-admin}',
        email='${SUPERUSER_EMAIL:-admin@flvs.local}',
        password='${SUPERUSER_PASSWORD:-changeme123}'
    )
    print("Superuser created!")
else:
    print("Superuser already exists.")
EOF
fi

# Execute command
exec "$@"
