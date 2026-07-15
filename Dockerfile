# =============================================================================
# FLVS - Feuerwehr Lagerverwaltungssystem
# Multi-Stage Docker Build
# =============================================================================

FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client
    libpq-dev \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    # PDF processing
    poppler-utils \
    # OCR (Tesseract)
    tesseract-ocr \
    tesseract-ocr-deu \
    # File type detection
    libmagic1 \
    # Build essentials (for pip packages)
    gcc \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Production Stage
# =============================================================================
FROM base as production

WORKDIR /app

# Create non-root user for security
RUN groupadd -r flvs && useradd -r -g flvs flvs

# Copy requirements first (Docker cache optimization)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and make entrypoint executable
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chmod +x /app/docker/scripts/entrypoint.sh \
    && chown -R flvs:flvs /app

# Collect static files (initial collection, entrypoint will update)
RUN python manage.py collectstatic --noinput --settings=flvs_project.settings.production || true

# Switch to non-root user
USER flvs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Entrypoint handles migrations and startup tasks
ENTRYPOINT ["/app/docker/scripts/entrypoint.sh"]

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "flvs_project.wsgi:application"]

# =============================================================================
# Celery Worker Stage
# =============================================================================
FROM production as celery-worker

# Der HTTP-Healthcheck aus der production-Stage (GET /health/ auf Port 8000) passt hier
# nicht – ein Worker hat keinen Webserver. Stattdessen über den Broker anpingen.
HEALTHCHECK --interval=60s --timeout=15s --start-period=60s --retries=3 \
    CMD celery -A flvs_project inspect ping | grep -q pong || exit 1

USER flvs
CMD ["celery", "-A", "flvs_project", "worker", "--loglevel=info"]

# =============================================================================
# Celery Beat Stage
# =============================================================================
FROM production as celery-beat

# Beat ist kein Worker (kein "inspect ping") und hat keinen Health-Endpunkt. Den geerbten
# HTTP-Healthcheck deaktivieren, damit der Container nicht dauerhaft "unhealthy" zeigt.
HEALTHCHECK NONE

USER flvs
CMD ["celery", "-A", "flvs_project", "beat", "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]
