# Security Audit - FLVS

**Datum:** 2025-10-03
**Phase:** 8 - Production Readiness
**Zweck:** Umfassender Security-Review vor Production-Deployment

---

## 1. Django Settings Security

### A. Production Settings Checklist

**File:** `/flvs_project/settings/production.py`

```python
# ✅ MUSS in Production konfiguriert sein:

# 1. DEBUG ausschalten
DEBUG = False  # ✅ KRITISCH!

# 2. SECRET_KEY aus Environment
SECRET_KEY = env('SECRET_KEY')  # ✅ Niemals hardcoded!

# 3. ALLOWED_HOSTS konfigurieren
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # z.B. ['lager.resqware.de']

# 4. HTTPS/SSL Enforcement
SECURE_SSL_REDIRECT = True  # ✅ Alle HTTP → HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 5. Cookie Security
SESSION_COOKIE_SECURE = True  # ✅ Nur über HTTPS
CSRF_COOKIE_SECURE = True     # ✅ Nur über HTTPS
SESSION_COOKIE_HTTPONLY = True  # ✅ Kein JavaScript-Zugriff
CSRF_COOKIE_HTTPONLY = True

# 6. HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 Jahr
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 7. Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True  # ✅ X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = 'DENY'             # ✅ Clickjacking-Schutz

# 8. Browser Security
SECURE_BROWSER_XSS_FILTER = True    # ✅ XSS-Filter aktivieren
```

### B. Zusätzliche Production-Settings

```python
# CSRF-Schutz
CSRF_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_AGE = 31449600  # 1 Jahr

# Session Security
SESSION_COOKIE_AGE = 1209600  # 2 Wochen
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20971520  # 20 MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Admin Security
ADMIN_URL = env('ADMIN_URL', default='admin/')  # Geheimer Admin-Pfad empfohlen
```

---

## 2. Authentifizierung & Autorisierung

### A. Password Validators (BEREITS KONFIGURIERT ✅)

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 10,  # ✅ Stark genug
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### B. Brute-Force Protection (BEREITS KONFIGURIERT ✅)

```python
# Django Axes - Brute-Force Protection
AXES_FAILURE_LIMIT = 5  # ✅ Nach 5 Fehlversuchen sperren
AXES_COOLOFF_TIME = 1   # ✅ 1 Stunde Sperre
AXES_ENABLE_ACCESS_FAILURE_LOG = True  # ✅ Logging
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
```

### C. 2FA für BTM-Beauftragte

**Status:** Infrastruktur vorhanden (django-otp installiert) ✅

**Implementierungs-Bedarf:**
```python
# permissions/decorators.py
from django_otp.decorators import otp_required

def btm_permission_required(permission):
    """
    BTM-Berechtigung + 2FA-Pflicht
    """
    def decorator(view_func):
        @permission_required(permission)
        @otp_required  # ✅ Zusätzliche 2FA-Prüfung
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

**Prüfung:**
- [ ] 2FA für BTM-Beauftragte aktivieren
- [ ] QR-Code-Setup für TOTP
- [ ] Backup-Codes generieren

---

## 3. SQL Injection Protection

### ✅ STATUS: SICHER

**Grund:** Django ORM verhindert SQL-Injection automatisch

**Kritische Stellen prüfen:**

```python
# ❌ UNSICHER (Raw SQL ohne Parameterisierung):
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ SICHER (Parameterisierte Queries):
cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])

# ✅ SICHER (Django ORM - immer sicher):
User.objects.filter(id=user_id)
```

**Audit-Befund:**
- ✅ Alle Models nutzen Django ORM
- ✅ Keine Raw-SQL-Queries gefunden
- ⚠️ **PRÜFUNG ERFORDERLICH:** Reporting App (`query`-Feld in ReportTemplate/KPI)

**Empfehlung für Reporting:**
```python
# reporting/utils.py
import re
from django.db import connection

ALLOWED_SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY',
    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN'
]

FORBIDDEN_SQL_KEYWORDS = [
    'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
    'TRUNCATE', 'EXEC', 'EXECUTE'
]

def validate_report_query(query):
    """Validiert Query vor Ausführung"""
    query_upper = query.upper()

    # Verbotene Keywords prüfen
    for keyword in FORBIDDEN_SQL_KEYWORDS:
        if keyword in query_upper:
            raise ValueError(f"Forbidden keyword: {keyword}")

    # Nur SELECT erlauben
    if not query_upper.strip().startswith('SELECT'):
        raise ValueError("Only SELECT queries allowed")

    return True

def execute_safe_query(query, params=None):
    """Führt Query sicher aus"""
    validate_report_query(query)

    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchall()
```

---

## 4. XSS (Cross-Site Scripting) Protection

### ✅ STATUS: SICHER (Django Template Auto-Escaping)

**Django Templates escapen automatisch:**
```django
{{ user.name }}  {# ✅ Automatisch escaped #}
{{ user.name|safe }}  {# ⚠️ NUR wenn vertrauenswürdig! #}
```

**Kritische Stellen prüfen:**

```python
# ❌ UNSICHER (format_html ohne Escaping):
format_html('<div>{}</div>', unsafe_html)

# ✅ SICHER (format_html escaped automatisch):
format_html('<div>{}</div>', user_input)  # ✅ user_input wird escaped

# ✅ SICHER (HTML-Tags explizit):
format_html('<div class="{}">{}</div>', css_class, text)
```

**Audit-Befund:**
- ✅ Alle Admin-Badges nutzen `format_html()` korrekt
- ✅ Keine `mark_safe()` in User-Input
- ✅ Templates nutzen Auto-Escaping

---

## 5. CSRF (Cross-Site Request Forgery) Protection

### ✅ STATUS: AKTIVIERT

**Django CSRF-Middleware aktiv:**
```python
MIDDLEWARE = [
    'django.middleware.csrf.CsrfViewMiddleware',  # ✅
]
```

**HTMX-Integration:**
```javascript
// static/js/htmx-csrf.js
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
});
```

**Prüfung:**
- ✅ Alle Forms haben `{% csrf_token %}`
- ✅ AJAX-Requests senden CSRF-Token
- ✅ API nutzt JWT-Auth (CSRF-frei)

---

## 6. File Upload Security

### A. Validierung

**Status:** Teilweise implementiert

**Empfohlene Verbesserungen:**

```python
# core/validators.py
import magic
from django.core.exceptions import ValidationError

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

def validate_file_upload(file):
    """Validiert hochgeladene Dateien"""
    # Dateigröße prüfen
    if file.size > MAX_FILE_SIZE:
        raise ValidationError(f"Datei zu groß (max {MAX_FILE_SIZE/1024/1024}MB)")

    # MIME-Type prüfen (anhand tatsächlicher Datei, nicht Extension!)
    mime = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Reset für weitere Verarbeitung

    if mime not in ALLOWED_MIME_TYPES:
        raise ValidationError(f"Dateityp nicht erlaubt: {mime}")

    return True
```

**In Models nutzen:**
```python
# documents/models.py
from core.validators import validate_file_upload

class Document(AuditedModel):
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        validators=[validate_file_upload]  # ✅
    )
```

### B. Sichere File-Pfade

```python
import os
from django.utils.text import get_valid_filename

def safe_upload_path(instance, filename):
    """Generiert sicheren Upload-Pfad"""
    # Filename sanitizen
    filename = get_valid_filename(filename)

    # Zufälligen Prefix hinzufügen (verhindert Überschreiben)
    import uuid
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"

    # In Jahres-/Monats-Struktur ablegen
    from datetime import datetime
    now = datetime.now()
    return f"documents/{now.year}/{now.month:02d}/{filename}"
```

---

## 7. BTM-Bereich Security (Vier-Augen-Prinzip)

### A. Implementierungs-Status

**Medical App - BTM-Security:**

```python
# medical/models.py - MedicalStockMovement

class MedicalStockMovement(AbstractStockMovement):
    # ✅ Vier-Augen-Prinzip implementiert
    requires_approval = models.BooleanField(default=False)
    approval_status = models.CharField(...)
    approved_by = models.ForeignKey(User, ...)
    approved_at = models.DateTimeField(...)

    # ✅ Approval-Request
    def request_approval(self, requested_by):
        if not self.item.is_btm:
            return False

        self.approval_status = BTMApprovalStatus.PENDING
        # TODO: Notification an BTM-Beauftragte senden
        self.save()
        return True

    # ✅ Approval durchführen
    def approve(self, approved_by):
        # Prüfen: approved_by != created_by (Vier-Augen!)
        if approved_by == self.user:
            raise ValidationError("Vier-Augen-Prinzip: Genehmiger != Ersteller")

        # Prüfen: approved_by hat BTM-Berechtigung
        if not approved_by.has_perm('medical.approve_btm_movement'):
            raise PermissionDenied("Keine BTM-Berechtigung")

        self.approval_status = BTMApprovalStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()

        # Bestand aktualisieren
        self.item.adjust_quantity(...)
```

### B. Security-Prüfung BTM

**Checklist:**
- [x] Vier-Augen-Prinzip implementiert (approved_by != user)
- [x] BTM-Permission existiert (`medical.approve_btm_movement`)
- [x] Approval-Status-Tracking (PENDING/APPROVED/REJECTED)
- [ ] **TODO:** 2FA-Pflicht für BTM-Beauftragte
- [ ] **TODO:** Audit-Log für alle BTM-Zugriffe
- [x] Admin-Interface zeigt BTM-Status

### C. Audit-Logging für BTM

**Empfehlung:**
```python
# medical/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

btm_logger = logging.getLogger('btm_audit')

@receiver(post_save, sender=MedicalStockMovement)
def log_btm_movement(sender, instance, created, **kwargs):
    """Loggt alle BTM-Bewegungen"""
    if instance.item.is_btm:
        btm_logger.info(
            "BTM_MOVEMENT",
            extra={
                'item_id': instance.item.id,
                'item_name': instance.item.name,
                'movement_type': instance.movement_type,
                'quantity': instance.quantity,
                'user_id': instance.user.id,
                'user_name': instance.user.get_full_name(),
                'approval_status': instance.approval_status,
                'approved_by_id': instance.approved_by.id if instance.approved_by else None,
                'timestamp': instance.movement_date.isoformat(),
                'ip_address': instance.user_ip,  # TODO: IP-Tracking hinzufügen
            }
        )
```

**Logging-Konfiguration:**
```python
# settings/production.py
LOGGING = {
    'loggers': {
        'btm_audit': {
            'handlers': ['btm_file'],
            'level': 'INFO',
            'propagate': False,
        }
    },
    'handlers': {
        'btm_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'btm_audit.log',
            'maxBytes': 1024 * 1024 * 100,  # 100 MB
            'backupCount': 50,  # 50 Backups = ~5 GB
            'formatter': 'json',
        }
    }
}
```

---

## 8. Permission-System Audit

### A. Berechtigungs-Hierarchie (aus PERMISSIONS.md)

```
Superuser (Django Admin)
├── Administrator (Vollzugriff alle Module)
├── Modulverantwortlicher (CRUD für zugewiesene Module)
├── Lagerverwalter (CR für Lager, UD nach Freigabe)
├── Werkstattmeister (Spezialrechte KFZ)
├── BTM-Beauftragter (Zugriff BTM-Bereich)
├── Wachleiter (Read-All, Fahrzeugübernahme)
└── Standard-Nutzer (Read für zugewiesene Bereiche)
```

### B. Custom Permissions Prüfung

**Medical App:**
```python
# medical/models.py
class Meta:
    permissions = [
        ('approve_btm_movement', 'Can approve BTM movements'),
        ('view_btm_items', 'Can view BTM items'),
        ('dispose_btm', 'Can dispose BTM items'),
    ]
```

**Prüfung:**
- [x] Custom Permissions definiert
- [ ] **TODO:** Management Command `setup_permissions` ausführen
- [ ] **TODO:** Rollen mit Permissions zuweisen

### C. Object-Level Permissions (Django Guardian)

**Status:** Infrastruktur vorhanden ✅

**Beispiel-Nutzung:**
```python
from guardian.shortcuts import assign_perm, remove_perm

# Dokument nur für bestimmte User sichtbar
document = Document.objects.get(id=1)
assign_perm('view_document', user, document)

# In View prüfen:
from guardian.decorators import permission_required_or_403

@permission_required_or_403('documents.view_document', (Document, 'id', 'document_id'))
def document_detail(request, document_id):
    ...
```

---

## 9. API Security

### A. JWT-Authentifizierung (BEREITS KONFIGURIERT ✅)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # ✅
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # ✅ Default: Auth required
    ],
}
```

### B. Rate Limiting

**EMPFOHLEN:**
```python
# settings/production.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',   # Anonyme Requests
        'user': '1000/hour',  # Authentifizierte User
    }
}
```

### C. API-Endpoint-Permissions

```python
# api/views.py
from rest_framework.permissions import IsAuthenticated
from permissions.permissions import ModulePermission

class MedicalItemViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ModulePermission]
    required_permission = 'medical.view_medicalitem'

    def get_queryset(self):
        # Nur eigene Locations sichtbar
        user_locations = self.request.user.get_accessible_locations()
        return MedicalItem.objects.filter(location__in=user_locations)
```

---

## 10. Dependency Security

### A. Bekannte Vulnerabilities prüfen

```bash
# Safety-Check für Python-Dependencies
pip install safety
safety check

# Oder:
pip-audit
```

### B. Regelmäßige Updates

**Kritische Packages:**
- Django (Security-Updates!)
- django-rest-framework
- Pillow (Image-Processing-Vulnerabilities)
- psycopg2 (PostgreSQL)

**Update-Strategie:**
```bash
# Monatlich prüfen:
pip list --outdated

# Security-Updates sofort:
pip install --upgrade Django
```

---

## 11. Environment-Variablen

### A. Sensitive Daten NIEMALS in Code

**✅ GUT (.env):**
```env
SECRET_KEY=xxx
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
EMAIL_HOST_PASSWORD=xxx
BACKUP_ENCRYPTION_KEY=xxx
```

**❌ SCHLECHT (settings.py):**
```python
SECRET_KEY = 'django-insecure-hardcoded-key'  # ❌ NIEMALS!
```

### B. .env-Template (.env.example)

**Erstellt:** ✅ (in README.md dokumentiert)

**Prüfung:**
- [x] .env.example vorhanden
- [ ] .env in .gitignore
- [ ] Production-Server: .env mit realen Secrets

---

## 12. Backup & Disaster Recovery

### A. Backup-Strategie

**Definiert in CLAUDE.md:**
- Täglich: Vollbackup PostgreSQL (pg_dump)
- Stündlich: Incremental WAL-Archivierung
- Weekly: Media-Files
- Retention: 30 Tage täglich, 12 Monate wöchentlich
- **Verschlüsselung:** AES-256

### B. Backup-Verschlüsselung

```bash
# Verschlüsseltes Backup
pg_dump flvs | gzip | \
  openssl enc -aes-256-cbc -salt -pbkdf2 -pass pass:$BACKUP_KEY \
  > backup_$(date +%Y%m%d).sql.gz.enc

# Entschlüsseln
openssl enc -aes-256-cbc -d -pbkdf2 -pass pass:$BACKUP_KEY \
  -in backup_20251003.sql.gz.enc | gunzip | psql flvs
```

---

## 13. Security-Monitoring

### A. Failed Login Attempts

**Django Axes:** ✅ Bereits konfiguriert

**Monitoring:**
```python
# Check for locked-out IPs
from axes.models import AccessAttempt

suspicious_ips = AccessAttempt.objects.filter(
    failures_since_start__gte=3
).values('ip_address').distinct()
```

### B. Unusual BTM Access

```python
# Celery Periodic Task
@shared_task
def detect_unusual_btm_access():
    """Erkennt ungewöhnliche BTM-Zugriffe"""
    from medical.models import MedicalStockMovement
    from django.utils import timezone

    # Mehr als 5 BTM-Bewegungen pro User pro Tag?
    today = timezone.now().date()
    movements = MedicalStockMovement.objects.filter(
        item__is_btm=True,
        movement_date__date=today
    ).values('user').annotate(
        count=Count('id')
    ).filter(count__gte=5)

    for mov in movements:
        # Alert senden
        send_security_alert(
            f"Ungewöhnliche BTM-Aktivität: User {mov['user']} hat {mov['count']} BTM-Bewegungen heute"
        )
```

---

## 14. Production-Deployment Checklist

### Pre-Deployment

- [ ] `DEBUG = False` in production.py
- [ ] `SECRET_KEY` aus Environment
- [ ] `ALLOWED_HOSTS` konfiguriert
- [ ] Alle SSL/HTTPS-Settings aktiviert
- [ ] HSTS aktiviert
- [ ] Database-Backups getestet
- [ ] .env-Datei auf Server (nicht in Git!)
- [ ] Migrations alle angewendet
- [ ] Static-Files gesammelt
- [ ] Permissions setup ausgeführt
- [ ] Superuser erstellt
- [ ] 2FA für BTM-Beauftragte aktiviert

### Post-Deployment

- [ ] SSL-Zertifikat verifiziert (https://)
- [ ] Admin-Login funktioniert
- [ ] API-Endpoints getestet
- [ ] Backup-Cronjob läuft
- [ ] Monitoring aktiv (Sentry/Prometheus)
- [ ] Log-Rotation konfiguriert
- [ ] Firewall-Regeln gesetzt (nur 80/443/22)

---

## 15. Sicherheits-Incidents Response Plan

### A. BTM-Zugriff ohne Berechtigung

1. **Sofort:** Betroffenen User deaktivieren
2. **Audit:** BTM-Logs der letzten 30 Tage prüfen
3. **Benachrichtigung:** Verantwortliche informieren
4. **Dokumentation:** Incident-Report erstellen

### B. Verdächtige Login-Aktivität

1. **IP sperren:** Axes Lockout
2. **User benachrichtigen:** Passwort-Reset erzwingen
3. **Logs prüfen:** Erfolgreiche Logins von dieser IP?
4. **Eskalieren:** Bei erfolgreichen Zugriffen

### C. Daten-Leak

1. **System offline:** Sofortiger Shutdown
2. **Forensik:** Logs sichern
3. **Behörden informieren:** DSGVO-Meldepflicht (72h)
4. **Betroffene benachrichtigen**

---

## 16. Security-Training

### Für Entwickler

- [ ] OWASP Top 10 (https://owasp.org/www-project-top-ten/)
- [ ] Django Security Best Practices
- [ ] SQL-Injection-Prevention
- [ ] XSS-Prevention

### Für Admins

- [ ] BTM-Vier-Augen-Prinzip
- [ ] Passwort-Management
- [ ] 2FA-Einrichtung
- [ ] Incident-Response

---

## 17. Action Items - Priorisiert

### 🔴 Kritisch (Vor Production!)

1. **DEBUG = False** in production.py setzen
2. **2FA für BTM-Beauftragte** aktivieren
3. **File-Upload-Validierung** implementieren
4. **BTM-Audit-Logging** aktivieren
5. **Backup-Test** durchführen

### 🟡 Wichtig (Erste Woche Production)

6. **Rate Limiting** für API
7. **Security-Monitoring** (Sentry)
8. **IP-Tracking** für BTM-Zugriffe
9. **Dependency-Audit** (safety check)
10. **SSL-Zertifikat** verifizieren

### 🟢 Optional (Nice-to-have)

11. **Penetration-Test** durch externes Team
12. **Security-Headers** erweitern (CSP, etc.)
13. **WAF** (Web Application Firewall)
14. **DDoS-Protection** (Cloudflare)

---

**Status:** 📋 Security-Audit abgeschlossen
**Kritische Findings:** 5 (siehe Action Items Rot)
**Nächster Security-Review:** Nach 3 Monaten Production
