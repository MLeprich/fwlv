"""
Basis-Settings für FLVS (Feuerwehr Lagerverwaltungssystem)
Settings die in allen Umgebungen (dev, prod) gleich sind
"""

from pathlib import Path
import environ
import os

# Environment-Variablen initialisieren
env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# .env Datei einlesen
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'lager.resqware.de'])


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    # Admin Interface
    'admin_interface',
    'colorfield',

    # Security & Permissions
    'guardian',
    'axes',
    'django_otp',
    'django_otp.plugins.otp_totp',

    # Forms
    'crispy_forms',
    'crispy_tailwind',

    # API
    'rest_framework',
    'rest_framework.authtoken',  # Token Authentication
    'rest_framework_simplejwt',
    'django_filters',
    'drf_spectacular',

    # Background Tasks
    'django_celery_beat',
    'django_celery_results',

    # Import/Export
    'import_export',

    # Tree Structure
    'mptt',
]

LOCAL_APPS = [
    'core.apps.CoreConfig',
    'permissions.apps.PermissionsConfig',
    'locations.apps.LocationsConfig',
    'personnel.apps.PersonnelConfig',
    'vehicles.apps.VehiclesConfig',
    'audit.apps.AuditConfig',
    'notifications.apps.NotificationsConfig',
    'inventory_base.apps.InventoryBaseConfig',
    'magazine.apps.MagazineConfig',
    'medical.apps.MedicalConfig',
    'clothing.apps.ClothingConfig',
    'equipment.apps.EquipmentConfig',
    'workshop.apps.WorkshopConfig',
    'disinfection.apps.DisinfectionConfig',
    'height_rescue.apps.HeightRescueConfig',
    'diving.apps.DivingConfig',
    'it_hardware.apps.ItHardwareConfig',
    'vehicle_handover.apps.VehicleHandoverConfig',
    'procurement.apps.ProcurementConfig',
    'inventory_check.apps.InventoryCheckConfig',
    'documents.apps.DocumentsConfig',
    'reporting.apps.ReportingConfig',
    'info_monitors.apps.InfoMonitorsConfig',
    'driving_license.apps.DrivingLicenseConfig',
    'organization.apps.OrganizationConfig',
    'wiki.apps.WikiConfig',
    'tickets.apps.TicketsConfig',
    'defect_management.apps.DefectManagementConfig',
    'civil_protection.apps.CivilProtectionConfig',
    'idcards.apps.IdcardsConfig',
    'objektverwaltung.apps.ObjektverwaltungConfig',
    'accident_report.apps.AccidentReportConfig',
    'surveys.apps.SurveysConfig',
    # Weitere Apps werden hier hinzugefuegt
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'core.middleware.ContentSecurityPolicyMiddleware',  # CSP für Tailwind CDN - MUST BE FIRST
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static Files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',  # 2FA Support
    'core.middleware.QRCodeScannerMiddleware',  # QR-Code/Barcode Scanner Redirect
    'core.middleware.PasswordChangeRequiredMiddleware',  # Force password change for new users
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # Brute-Force Protection
]

ROOT_URLCONF = 'flvs_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                # Custom Context Processors
                'core.context_processors.notification_count',
                'core.context_processors.app_settings',
                'core.context_processors.user_permissions',
                'core.context_processors.module_badges',
                'core.context_processors.user_settings_context',
                'core.context_processors.module_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'flvs_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}


# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Login URLs
LOGIN_URL = 'core:login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'core:login'


# Personnel Settings
# Standard-Passwort für neue Benutzer (wird bei erster Anmeldung geändert)
PERSONNEL_DEFAULT_PASSWORD = env('PERSONNEL_DEFAULT_PASSWORD', default='Feuerwehr.0112')


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'de-de'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Whitenoise Configuration
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ============================================================================
# CRISPY FORMS SETTINGS
# ============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"


# ============================================================================
# DJANGO GUARDIAN (Object-Level Permissions)
# ============================================================================

AUTHENTICATION_BACKENDS = (
    'axes.backends.AxesStandaloneBackend',  # django-axes für Brute-Force Protection
    'permissions.backends.CombinedPermissionBackend',  # Custom: Zeitbasierte + Delegierte Permissions
    'guardian.backends.ObjectPermissionBackend',  # django-guardian für Object-Level Permissions
    'django.contrib.auth.backends.ModelBackend',  # Fallback: Standard Django Auth
)


# ============================================================================
# DJANGO AXES (Brute-Force Protection)
# ============================================================================

# Abschaltbar über die .env (AXES_ENABLED=false) – gedacht für abgeschottete interne
# Netze ohne Internetzugang (z.B. Stadt-VM), wo eine Login-Sperre mehr Betriebsstörung
# als Schutz ist. Standard: aktiv. Ein leer durchgereichter Wert (Compose-Default für
# "nicht gesetzt") zählt als "nicht gesetzt" und lässt den Schutz an.
_axes_enabled = os.environ.get('AXES_ENABLED', '').strip()
AXES_ENABLED = _axes_enabled.lower() not in ('false', '0', 'no', 'off') if _axes_enabled else True

AXES_FAILURE_LIMIT = 5  # Anzahl fehlgeschlagene Login-Versuche
AXES_COOLOFF_TIME = 1  # Stunden bis Reset
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True

# Hinter einem Reverse-Proxy (oder lokalem nginx) sehen alle Clients für Django gleich
# aus – eine einzige IP. Mit dem axes-Default "Sperre je IP" sperren 5 Fehlversuche von
# IRGENDWEM sämtliche Nutzer aus. Deshalb je Kombination aus Benutzername UND IP sperren:
# ein Konto lässt sich weiterhin nicht durchprobieren, aber niemand sperrt alle anderen.
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]


# ============================================================================
# REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}


# ============================================================================
# DRF SPECTACULAR (OpenAPI/Swagger)
# ============================================================================

SPECTACULAR_SETTINGS = {
    'TITLE': 'FLVS API',
    'DESCRIPTION': 'Feuerwehr Lagerverwaltungssystem REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}


# ============================================================================
# CELERY
# ============================================================================

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True

# Celery Beat (Periodic Tasks)
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


# ============================================================================
# CACHE (Redis)
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session in Redis speichern
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


# ============================================================================
# EMAIL SETTINGS
# ============================================================================

EMAIL_BACKEND = env(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@flvs.local')


# ============================================================================
# LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'flvs.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose'
        },
        'audit_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'flvs': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}
