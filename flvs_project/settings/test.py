"""
Test-Settings: nutzen SQLite (in-memory), damit pytest unabhängig vom
Postgres-User Tests laufen lassen kann.
"""

from .base import *  # noqa: F401, F403


DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Static-Files unhashed im Test — sonst müsste collectstatic vor jedem
# pytest-Run laufen, und {% static %}-URLs würden nicht zu den Asset-Namen
# matchen, gegen die Tests prüfen.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Schnellere Tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

# Cache deaktivieren
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
}

# E-Mails verschlucken
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Session/CSRF auf nicht-secure
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Axes (Brute-Force) und CSP-Middleware sind im Test-Setting unkritisch.
