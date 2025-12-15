#!/bin/bash
# =============================================================================
# FLVS - Docker Entrypoint Script
# =============================================================================
# Handles database waiting, migrations, static files, and startup

set -e

echo "=========================================="
echo "FLVS - Feuerwehr Lagerverwaltungssystem"
echo "=========================================="
echo "Command: $@"

# Determine if this is the web container (runs migrations) or worker container
COMMAND="$1"
IS_WEB_CONTAINER=false

if [[ "$COMMAND" == "gunicorn" ]] || [[ "$COMMAND" == "" ]]; then
    IS_WEB_CONTAINER=true
fi

# Function to wait for a service
wait_for_service() {
    local service=$1
    local check_cmd=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo "Waiting for $service..."
    while ! eval "$check_cmd" 2>/dev/null; do
        if [ $attempt -ge $max_attempts ]; then
            echo "ERROR: $service not available after $max_attempts attempts"
            exit 1
        fi
        echo "  Attempt $attempt/$max_attempts - $service not ready, waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "$service is ready!"
}

# Wait for database
if [ -n "$DATABASE_URL" ]; then
    wait_for_service "PostgreSQL" "python -c \"import psycopg2; psycopg2.connect('$DATABASE_URL')\""
fi

# Wait for Redis
if [ -n "$REDIS_URL" ]; then
    wait_for_service "Redis" "python -c \"import redis; redis.from_url('$REDIS_URL').ping()\""
fi

# Only run migrations and collectstatic for the main web container
if [ "$IS_WEB_CONTAINER" = true ]; then
    echo ""
    echo "Running startup tasks for web container..."

    # Run migrations
    echo "Running database migrations..."
    python manage.py migrate --noinput

    # Collect static files
    echo "Collecting static files..."
    python manage.py collectstatic --noinput

    # Create superuser if requested and not exists
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        echo "Checking for superuser..."
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = '${SUPERUSER_USERNAME:-admin}'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email='${SUPERUSER_EMAIL:-admin@flvs.local}',
        password='${SUPERUSER_PASSWORD:-changeme123}'
    )
    print(f"Superuser '{username}' created!")
else:
    print(f"User '{username}' already exists.")
EOF
    fi

    echo ""
    echo "Startup tasks completed!"
else
    echo "Worker container - skipping migrations and collectstatic"
fi

echo "=========================================="
echo "Starting: $@"
echo "=========================================="

# Execute the main command
exec "$@"
