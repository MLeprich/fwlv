# FLVS Production Deployment Guide

**Version:** 1.0
**Letzte Aktualisierung:** 2025-10-03
**Für:** Ubuntu Server 20.04+ | PostgreSQL 15+ | Redis | Nginx

---

## Übersicht

Dieser Guide beschreibt den kompletten Production-Deployment-Prozess für FLVS (Feuerwehr Lagerverwaltungssystem).

**Deployment-Architektur:**
```
Internet
    ↓
Nginx (Reverse Proxy, SSL-Termination)
    ↓
Gunicorn (WSGI Server) → Django Application
    ↓
PostgreSQL (Database) + Redis (Cache/Celery)
    ↓
Celery Worker + Celery Beat (Background Tasks)
```

---

## Voraussetzungen

### Server-Anforderungen

**Minimum:**
- **CPU:** 2 Cores
- **RAM:** 4 GB
- **Disk:** 50 GB SSD
- **OS:** Ubuntu Server 20.04 LTS oder neuer

**Empfohlen (Production):**
- **CPU:** 4 Cores
- **RAM:** 8 GB
- **Disk:** 100 GB SSD (+ separates Backup-Volume)
- **OS:** Ubuntu Server 22.04 LTS

### Software-Versionen

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx 1.18+
- Node.js 18+ (für Frontend-Build, optional)

---

## Teil 1: Server-Vorbereitung

### 1.1 System-Update

```bash
# Als root oder mit sudo
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
```

### 1.2 Firewall konfigurieren

```bash
# UFW installieren (falls nicht vorhanden)
sudo apt install ufw

# Standard-Policy: Deny All
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Essenzielle Ports öffnen
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# Firewall aktivieren
sudo ufw enable
sudo ufw status
```

### 1.3 System-Pakete installieren

```bash
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    build-essential \
    libpq-dev \
    libmagic1 \
    supervisor
```

---

## Teil 2: PostgreSQL Setup

### 2.1 PostgreSQL Datenbank erstellen

```bash
# Als postgres-User
sudo -u postgres psql

# In psql:
CREATE DATABASE flvs;
CREATE USER flvs_user WITH PASSWORD 'IHR_SICHERES_PASSWORT_HIER';

ALTER ROLE flvs_user SET client_encoding TO 'utf8';
ALTER ROLE flvs_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE flvs_user SET timezone TO 'Europe/Berlin';

GRANT ALL PRIVILEGES ON DATABASE flvs TO flvs_user;

-- PostgreSQL 15+ zusätzlich:
\c flvs
GRANT ALL ON SCHEMA public TO flvs_user;

\q
```

### 2.2 PostgreSQL Sicherheit

```bash
# PostgreSQL-Config editieren
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Nur lokale Verbindungen erlauben (Zeile hinzufügen):
# local   all   flvs_user   md5

# PostgreSQL neu starten
sudo systemctl restart postgresql
sudo systemctl enable postgresql
```

### 2.3 Datenbank-Backup-Script

```bash
# Backup-Directory erstellen
sudo mkdir -p /var/backups/flvs/database
sudo chown postgres:postgres /var/backups/flvs/database

# Backup-Script erstellen
sudo nano /usr/local/bin/backup-flvs-db.sh
```

**Inhalt:**
```bash
#!/bin/bash
# FLVS Database Backup Script

BACKUP_DIR="/var/backups/flvs/database"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Backup erstellen
sudo -u postgres pg_dump flvs | gzip > "${BACKUP_DIR}/flvs_${DATE}.sql.gz"

# Alte Backups löschen
find ${BACKUP_DIR} -type f -name "flvs_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup completed: flvs_${DATE}.sql.gz"
```

```bash
# Ausführbar machen
sudo chmod +x /usr/local/bin/backup-flvs-db.sh

# Cronjob hinzufügen (täglich 2 Uhr)
sudo crontab -e
# Zeile hinzufügen:
# 0 2 * * * /usr/local/bin/backup-flvs-db.sh >> /var/log/flvs-backup.log 2>&1
```

---

## Teil 3: Redis Setup

### 3.1 Redis konfigurieren

```bash
# Redis-Config editieren
sudo nano /etc/redis/redis.conf

# Wichtige Settings:
# bind 127.0.0.1 ::1       # Nur lokal
# maxmemory 512mb          # Max. RAM für Redis
# maxmemory-policy allkeys-lru  # LRU-Eviction

# Redis neu starten
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Testen
redis-cli ping
# Sollte "PONG" zurückgeben
```

---

## Teil 4: FLVS-Anwendung deployen

### 4.1 System-User erstellen

```bash
# Dedizierter User für FLVS
sudo useradd -m -s /bin/bash flvs
sudo usermod -aG www-data flvs
```

### 4.2 Projekt-Verzeichnis erstellen

```bash
# Als flvs-User
sudo mkdir -p /var/www/flvs
sudo chown flvs:www-data /var/www/flvs
sudo chmod 750 /var/www/flvs

# Zu flvs-User wechseln
sudo su - flvs
cd /var/www/flvs
```

### 4.3 Repository klonen

```bash
# Git-Repository klonen
git clone https://github.com/YOUR_ORG/flvs.git .

# Oder: Manuelle Übertragung via SCP/SFTP
```

### 4.4 Virtual Environment erstellen

```bash
# Python Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

# Pip upgrade
pip install --upgrade pip setuptools wheel
```

### 4.5 Dependencies installieren

```bash
# Python-Packages
pip install -r requirements.txt

# Production-specific (falls nicht in requirements.txt):
pip install gunicorn sentry-sdk
```

### 4.6 Environment-Variablen konfigurieren

```bash
# .env-Datei erstellen
nano .env
```

**Inhalt (.env):**
```env
# Django
DEBUG=False
SECRET_KEY=GENERIERE_EINEN_SICHEREN_SECRET_KEY_HIER
DJANGO_SETTINGS_MODULE=flvs_project.settings.production
ALLOWED_HOSTS=lager.resqware.de,www.lager.resqware.de

# Database
DATABASE_URL=postgresql://flvs_user:IHR_PASSWORT@localhost:5432/flvs

# Redis
REDIS_URL=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@lager.resqware.de
EMAIL_HOST_PASSWORD=EMAIL_PASSWORT_HIER
DEFAULT_FROM_EMAIL=noreply@lager.resqware.de

# Admin
ADMIN_EMAIL=admin@lager.resqware.de
ADMIN_URL=geheimer-admin-pfad-2025/

# Security (optional)
BTM_REQUIRE_2FA=True
SENTRY_DSN=https://...@sentry.io/...
```

**SECRET_KEY generieren:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4.7 Logs-Verzeichnis erstellen

```bash
mkdir -p /var/www/flvs/logs
chmod 750 /var/www/flvs/logs
```

### 4.8 Migrations ausführen

```bash
# Virtual Environment aktivieren
source /var/www/flvs/venv/bin/activate

# Migrations
python manage.py migrate

# Static-Files sammeln
python manage.py collectstatic --noinput

# Superuser erstellen
python manage.py createsuperuser
# Username: admin
# Email: admin@lager.resqware.de
# Password: SICHERES_PASSWORT

# Permissions setup
python manage.py setup_permissions
```

---

## Teil 5: Gunicorn Setup

### 5.1 Gunicorn-Config erstellen

```bash
nano /var/www/flvs/gunicorn_config.py
```

**Inhalt:**
```python
# Gunicorn Configuration
import multiprocessing

# Server Socket
bind = 'unix:/var/www/flvs/flvs.sock'
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '/var/www/flvs/logs/gunicorn-access.log'
errorlog = '/var/www/flvs/logs/gunicorn-error.log'
loglevel = 'info'

# Process Naming
proc_name = 'flvs_gunicorn'

# Server Mechanics
daemon = False  # Supervisor/systemd managed
pidfile = '/var/www/flvs/gunicorn.pid'
user = 'flvs'
group = 'www-data'
umask = 0o007

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
```

### 5.2 Systemd Service erstellen

```bash
# Als root
sudo nano /etc/systemd/system/flvs.service
```

**Inhalt:**
```ini
[Unit]
Description=FLVS Gunicorn Application Server
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=notify
User=flvs
Group=www-data
WorkingDirectory=/var/www/flvs
Environment="PATH=/var/www/flvs/venv/bin"
EnvironmentFile=/var/www/flvs/.env
ExecStart=/var/www/flvs/venv/bin/gunicorn \
    --config /var/www/flvs/gunicorn_config.py \
    flvs_project.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### 5.3 Service starten

```bash
# Systemd reload
sudo systemctl daemon-reload

# Service starten
sudo systemctl start flvs

# Service aktivieren (Auto-Start)
sudo systemctl enable flvs

# Status prüfen
sudo systemctl status flvs

# Socket prüfen
ls -la /var/www/flvs/flvs.sock
```

---

## Teil 6: Celery Setup

### 6.1 Celery Worker Service

```bash
sudo nano /etc/systemd/system/flvs-celery.service
```

**Inhalt:**
```ini
[Unit]
Description=FLVS Celery Worker
After=network.target redis.service
Requires=redis.service

[Service]
Type=forking
User=flvs
Group=www-data
WorkingDirectory=/var/www/flvs
Environment="PATH=/var/www/flvs/venv/bin"
EnvironmentFile=/var/www/flvs/.env
ExecStart=/var/www/flvs/venv/bin/celery -A flvs_project worker \
    --loglevel=info \
    --logfile=/var/www/flvs/logs/celery-worker.log \
    --pidfile=/var/run/celery/worker.pid \
    --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

### 6.2 Celery Beat Service (Scheduled Tasks)

```bash
sudo nano /etc/systemd/system/flvs-celery-beat.service
```

**Inhalt:**
```ini
[Unit]
Description=FLVS Celery Beat Scheduler
After=network.target redis.service
Requires=redis.service

[Service]
Type=forking
User=flvs
Group=www-data
WorkingDirectory=/var/www/flvs
Environment="PATH=/var/www/flvs/venv/bin"
EnvironmentFile=/var/www/flvs/.env
ExecStart=/var/www/flvs/venv/bin/celery -A flvs_project beat \
    --loglevel=info \
    --logfile=/var/www/flvs/logs/celery-beat.log \
    --pidfile=/var/run/celery/beat.pid \
    --schedule=/var/run/celery/celerybeat-schedule \
    --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

### 6.3 PID-Verzeichnis erstellen

```bash
sudo mkdir /var/run/celery
sudo chown flvs:www-data /var/run/celery
```

### 6.4 Services starten

```bash
# Services starten
sudo systemctl start flvs-celery
sudo systemctl start flvs-celery-beat

# Auto-Start aktivieren
sudo systemctl enable flvs-celery
sudo systemctl enable flvs-celery-beat

# Status prüfen
sudo systemctl status flvs-celery
sudo systemctl status flvs-celery-beat
```

---

## Teil 7: Nginx Setup

### 7.1 Nginx-Konfiguration erstellen

```bash
sudo nano /etc/nginx/sites-available/flvs
```

**Inhalt:**
```nginx
# FLVS Nginx Configuration

upstream flvs_app {
    server unix:/var/www/flvs/flvs.sock fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name lager.resqware.de www.lager.resqware.de;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name lager.resqware.de www.lager.resqware.de;

    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/lager.resqware.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lager.resqware.de/privkey.pem;

    # SSL Configuration (Mozilla Modern)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/flvs-access.log;
    error_log /var/log/nginx/flvs-error.log;

    # Client Body Size (für File-Uploads)
    client_max_body_size 20M;

    # Timeouts
    client_body_timeout 60s;
    client_header_timeout 60s;
    keepalive_timeout 65s;

    # Root
    root /var/www/flvs;

    # Static Files
    location /static/ {
        alias /var/www/flvs/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media Files
    location /media/ {
        alias /var/www/flvs/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
        alias /var/www/flvs/staticfiles/favicon.ico;
    }

    # robots.txt
    location = /robots.txt {
        access_log off;
        log_not_found off;
        alias /var/www/flvs/staticfiles/robots.txt;
    }

    # Application
    location / {
        proxy_pass http://flvs_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Deny access to sensitive files
    location ~ /\.(?!well-known) {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ /\.env {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### 7.2 Nginx aktivieren

```bash
# Symlink erstellen
sudo ln -s /etc/nginx/sites-available/flvs /etc/nginx/sites-enabled/

# Default-Site deaktivieren
sudo rm /etc/nginx/sites-enabled/default

# Konfiguration testen
sudo nginx -t

# Nginx neu starten
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## Teil 8: SSL-Zertifikat (Let's Encrypt)

### 8.1 Certbot installieren

```bash
sudo apt install certbot python3-certbot-nginx
```

### 8.2 SSL-Zertifikat erstellen

```bash
# Zertifikat für Domain
sudo certbot --nginx -d lager.resqware.de -d www.lager.resqware.de

# Folge den Prompts:
# - Email-Adresse angeben
# - Terms of Service akzeptieren
# - Redirect HTTP → HTTPS: Yes
```

### 8.3 Auto-Renewal testen

```bash
# Dry-Run
sudo certbot renew --dry-run

# Cronjob ist automatisch erstellt (2x täglich)
# Prüfen:
sudo systemctl list-timers | grep certbot
```

---

## Teil 9: Monitoring & Logging

### 9.1 Log-Rotation konfigurieren

```bash
sudo nano /etc/logrotate.d/flvs
```

**Inhalt:**
```
/var/www/flvs/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 flvs www-data
    sharedscripts
    postrotate
        systemctl reload flvs > /dev/null 2>&1 || true
    endscript
}
```

### 9.2 Fail2Ban (optional, empfohlen)

```bash
# Fail2Ban installieren
sudo apt install fail2ban

# Nginx-Jail aktivieren
sudo nano /etc/fail2ban/jail.local
```

**Inhalt:**
```ini
[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true

[nginx-noproxy]
enabled = true
```

```bash
# Fail2Ban starten
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

## Teil 10: Final Checks

### 10.1 Service-Status prüfen

```bash
# Alle Services prüfen
sudo systemctl status postgresql
sudo systemctl status redis
sudo systemctl status flvs
sudo systemctl status flvs-celery
sudo systemctl status flvs-celery-beat
sudo systemctl status nginx

# Logs prüfen
sudo journalctl -u flvs -n 50
sudo journalctl -u flvs-celery -n 50
tail -f /var/www/flvs/logs/gunicorn-error.log
tail -f /var/www/flvs/logs/celery-worker.log
```

### 10.2 Deployment-Checklist

- [ ] Alle Services laufen
- [ ] HTTPS funktioniert (https://lager.resqware.de)
- [ ] Static-Files werden geladen
- [ ] Admin-Login funktioniert
- [ ] Database-Verbindung OK
- [ ] Celery Tasks laufen
- [ ] File-Upload funktioniert
- [ ] Email-Versand funktioniert
- [ ] Backup-Cronjob läuft
- [ ] SSL-Zertifikat gültig
- [ ] Firewall konfiguriert

### 10.3 Security-Scan

```bash
# HTTPS-Qualität testen
# https://www.ssllabs.com/ssltest/

# Sicherheits-Headers prüfen
# https://securityheaders.com/
```

---

## Teil 11: Updates & Wartung

### 11.1 Code-Update deployen

```bash
# Als flvs-User
sudo su - flvs
cd /var/www/flvs

# Code aktualisieren
git pull origin main

# Virtual Environment aktivieren
source venv/bin/activate

# Dependencies aktualisieren
pip install -r requirements.txt --upgrade

# Migrations
python manage.py migrate

# Static-Files neu sammeln
python manage.py collectstatic --noinput

# Services neu starten
sudo systemctl restart flvs
sudo systemctl restart flvs-celery
sudo systemctl restart flvs-celery-beat
```

### 11.2 Database-Backup manuell

```bash
# Backup erstellen
/usr/local/bin/backup-flvs-db.sh

# Backup wiederherstellen
gunzip < /var/backups/flvs/database/flvs_20251003_020000.sql.gz | \
    sudo -u postgres psql flvs
```

---

## Teil 12: Troubleshooting

### Problem: Gunicorn startet nicht

```bash
# Logs prüfen
sudo journalctl -u flvs -n 100

# Socket-Permissions prüfen
ls -la /var/www/flvs/flvs.sock

# Manuell starten (Debug)
sudo su - flvs
cd /var/www/flvs
source venv/bin/activate
gunicorn --config gunicorn_config.py flvs_project.wsgi:application
```

### Problem: Static-Files nicht gefunden

```bash
# Collectstatic erneut ausführen
python manage.py collectstatic --clear --noinput

# Nginx-Permissions prüfen
ls -la /var/www/flvs/staticfiles/

# Nginx-Konfiguration testen
sudo nginx -t
```

### Problem: Celery-Tasks laufen nicht

```bash
# Celery-Status prüfen
sudo systemctl status flvs-celery

# Redis-Verbindung testen
redis-cli ping

# Celery-Logs prüfen
tail -f /var/www/flvs/logs/celery-worker.log
```

---

## Support & Kontakt

**Dokumentation:** /var/www/flvs/docs/
**Logs:** /var/www/flvs/logs/
**Backups:** /var/backups/flvs/

**Bei Problemen:**
1. Logs prüfen
2. Service-Status prüfen
3. Dokumentation konsultieren

---

**Deployment abgeschlossen! 🚀**

FLVS ist nun produktiv unter https://lager.resqware.de erreichbar.
