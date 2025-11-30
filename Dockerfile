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
    libgdk-pixbuf2.0-0 \
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

# Create necessary directories
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R flvs:flvs /app

# Collect static files
RUN python manage.py collectstatic --noinput --settings=flvs_project.settings.production || true

# Switch to non-root user
USER flvs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/')" || exit 1

# Default command (can be overridden in docker-compose)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "flvs_project.wsgi:application"]

# =============================================================================
# Celery Worker Stage
# =============================================================================
FROM production as celery-worker

USER flvs
CMD ["celery", "-A", "flvs_project", "worker", "--loglevel=info"]

# =============================================================================
# Celery Beat Stage
# =============================================================================
FROM production as celery-beat

USER flvs
CMD ["celery", "-A", "flvs_project", "beat", "--loglevel=info", "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler"]
