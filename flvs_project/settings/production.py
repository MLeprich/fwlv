"""
Production Settings für FLVS
Security-hardened für Production-Deployment
Basierend auf Security-Audit (docs/SECURITY_AUDIT.md)
"""

from .base import *  # noqa

# ============================================================================
# CRITICAL SECURITY SETTINGS
# ============================================================================

# DEBUG MUSS False sein in Production!
DEBUG = False

# SECRET_KEY aus Environment (NIEMALS hardcoded!)
SECRET_KEY = env('SECRET_KEY')

# Erlaubte Hosts
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['lager.resqware.de'])

# ============================================================================
# HTTPS / SSL ENFORCEMENT
# ============================================================================

# SSL kann deaktiviert werden für:
# - Initiale Installation ohne SSL-Zertifikat
# - Deployment hinter einem SSL-terminierenden Load Balancer
# - Test-Umgebungen
USE_SSL = env.bool('USE_SSL', default=True)

# Alle HTTP-Requests zu HTTPS umleiten
SECURE_SSL_REDIRECT = USE_SSL

# Proxy SSL-Header (wenn hinter Nginx/Apache)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if USE_SSL else None

# ============================================================================
# COOKIE SECURITY
# ============================================================================

# Session Cookies
SESSION_COOKIE_SECURE = USE_SSL  # Nur HTTPS wenn SSL aktiv
SESSION_COOKIE_HTTPONLY = True  # Kein JavaScript-Zugriff
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF-Schutz
SESSION_COOKIE_AGE = 1209600  # 2 Wochen

# CSRF Cookies
CSRF_COOKIE_SECURE = USE_SSL  # Nur HTTPS wenn SSL aktiv
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_AGE = 31449600  # 1 Jahr

# Session-Einstellungen
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ============================================================================
# HTTP STRICT TRANSPORT SECURITY (HSTS)
# ============================================================================

# Browser erzwingen HTTPS für 1 Jahr (nur wenn SSL aktiv)
SECURE_HSTS_SECONDS = 31536000 if USE_SSL else 0  # 1 Jahr
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_SSL
SECURE_HSTS_PRELOAD = USE_SSL

# ============================================================================
# CONTENT SECURITY
# ============================================================================

# X-Content-Type-Options: nosniff
SECURE_CONTENT_TYPE_NOSNIFF = True

# X-Frame-Options: DENY (Clickjacking-Schutz)
X_FRAME_OPTIONS = 'DENY'

# X-XSS-Protection
SECURE_BROWSER_XSS_FILTER = True

# ============================================================================
# FILE UPLOAD SECURITY
# ============================================================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB
FILE_UPLOAD_PERMISSIONS = 0o644

# ============================================================================
# ADMIN SECURITY
# ============================================================================

# Geheimer Admin-Pfad (aus Environment)
# Setze ADMIN_URL in .env z.B.: geheimer-admin-zugang/
ADMIN_URL = env('ADMIN_URL', default='admin/')

# ============================================================================
# DATABASE (Production)
# ============================================================================

# Connection Pooling
DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 Minuten

# PostgreSQL-specific options (only if using PostgreSQL)
if 'postgresql' in DATABASES['default'].get('ENGINE', '') or 'postgres' in env('DATABASE_URL', default=''):
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
    }

# ============================================================================
# CACHING (Redis - Performance)
# ============================================================================

CACHES['default']['OPTIONS']['CONNECTION_POOL_KWARGS'] = {
    'max_connections': 50,
    'retry_on_timeout': True,
}
CACHES['default']['KEY_PREFIX'] = 'flvs_prod'
CACHES['default']['TIMEOUT'] = 300  # 5 Minuten Default

# ============================================================================
# CELERY (Production)
# ============================================================================

CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# ============================================================================
# EMAIL (Production)
# ============================================================================

EMAIL_TIMEOUT = 10

# ============================================================================
# STATIC FILES (Whitenoise)
# ============================================================================

# STORAGES is already configured in base.py with whitenoise
# STATICFILES_STORAGE is deprecated in Django 4.2+ and conflicts with STORAGES

# ============================================================================
# LOGGING (Production - Enhanced)
# ============================================================================

# BTM-Audit-Logger hinzufügen
LOGGING['handlers']['btm_file'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'btm_audit.log',
    'maxBytes': 1024 * 1024 * 100,  # 100 MB
    'backupCount': 50,
    'formatter': 'verbose'
}

LOGGING['handlers']['security_file'] = {
    'level': 'WARNING',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'security.log',
    'maxBytes': 1024 * 1024 * 50,  # 50 MB
    'backupCount': 20,
    'formatter': 'verbose'
}

LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['flvs']['level'] = 'INFO'

LOGGING['loggers']['btm_audit'] = {
    'handlers': ['btm_file'],
    'level': 'INFO',
    'propagate': False,
}

LOGGING['loggers']['django.security'] = {
    'handlers': ['security_file'],
    'level': 'WARNING',
    'propagate': False,
}

# ============================================================================
# REST FRAMEWORK (API Security)
# ============================================================================

# Rate Limiting für API
REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle'
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',   # Anonyme Requests
    'user': '1000/hour',  # Authentifizierte User
}

# Nur JSON-Renderer (kein Browsable API)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]

# ============================================================================
# DJANGO AXES (Brute-Force Protection)
# ============================================================================

AXES_LOCKOUT_URL = '/locked/'
AXES_VERBOSE = True

# ============================================================================
# SENTRY (Error Tracking) - Optional
# ============================================================================

SENTRY_DSN = env('SENTRY_DSN', default=None)

if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                DjangoIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% der Requests tracken
            send_default_pii=False,  # Keine PII-Daten
            environment='production',
            release=env('GIT_COMMIT', default='unknown'),
        )
    except ImportError:
        pass  # Sentry SDK nicht installiert

# ============================================================================
# ADMINS & MANAGERS
# ============================================================================

ADMINS = [
    ('FLVS Admin', env('ADMIN_EMAIL', default='admin@flvs.local')),
]
MANAGERS = ADMINS

# ============================================================================
# PERFORMANCE OPTIMIZATIONS
# ============================================================================

# Template Loaders (cached) - must disable APP_DIRS when using loaders
TEMPLATES[0]['APP_DIRS'] = False
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Disable Debug Toolbar
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]

# ============================================================================
# CUSTOM SETTINGS (BTM, Reports, KPIs)
# ============================================================================

# BTM-Security
BTM_REQUIRE_2FA = env.bool('BTM_REQUIRE_2FA', default=True)
BTM_APPROVAL_TIMEOUT_HOURS = env.int('BTM_APPROVAL_TIMEOUT_HOURS', default=24)

# Report-Generierung
REPORT_MAX_EXECUTION_TIME = 300  # 5 Minuten
REPORT_RETENTION_DAYS = 30

# KPI-Refresh
KPI_DEFAULT_REFRESH_INTERVAL = 300  # 5 Minuten

# Widget-Cache
WIDGET_CACHE_TTL = 60  # 1 Minute

# ============================================================================
# PRODUCTION VALIDATION CHECKS
# ============================================================================

# Verhindere versehentliche Production-Starts mit unsicheren Settings
if DEBUG:
    raise RuntimeError("❌ DEBUG darf in production.py nicht True sein!")

if SECRET_KEY == 'django-insecure-change-this-in-production':
    raise RuntimeError("❌ SECRET_KEY muss in Production via Environment gesetzt werden!")

if not ALLOWED_HOSTS or ALLOWED_HOSTS == ['localhost', '127.0.0.1']:
    raise RuntimeError("❌ ALLOWED_HOSTS muss in Production korrekt gesetzt werden!")
