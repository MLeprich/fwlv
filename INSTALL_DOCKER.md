# FLVS - Docker Container Installation

Diese Anleitung beschreibt die Installation des Feuerwehr Lagerverwaltungssystems (FLVS) in einer Docker-Container-Umgebung auf einem Linux-System.

---

## Voraussetzungen

### Systemanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 2 Cores | 4 Cores |
| RAM | 4 GB | 8 GB |
| Speicher | 20 GB | 50 GB |
| OS | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS |

### Software-Voraussetzungen

- Docker Engine 24.0+
- Docker Compose v2.20+
- Git

### Docker & Docker Compose installieren (falls nicht vorhanden)

```bash
# Docker installieren (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Benutzer zur Docker-Gruppe hinzufügen
sudo usermod -aG docker $USER

# Docker Compose Plugin installieren (falls nicht enthalten)
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Versionen prüfen
docker --version
docker compose version

# Neuanmeldung erforderlich für Gruppenänderung
# Alternativ: newgrp docker
```

---

## Installation

### 1. Repository klonen

```bash
# In das gewünschte Verzeichnis wechseln
cd /opt

# Repository klonen
git clone https://github.com/MLeprich/fwlv.git flvs

# In das Projektverzeichnis wechseln
cd flvs
```

### 2. Umgebungsvariablen konfigurieren

```bash
# .env-Datei aus Vorlage erstellen
cp .env.example .env

# .env-Datei bearbeiten
nano .env
```

**Wichtige Einstellungen in `.env`:**

```bash
# =============================================================================
# PFLICHTFELDER - Diese MÜSSEN angepasst werden!
# =============================================================================

# Sicheren Secret Key generieren:
# python3 -c "import secrets; print(secrets.token_urlsafe(50))"
SECRET_KEY=ihr-sicherer-secret-key-hier

# Datenbank-Passwort (sicher wählen!)
POSTGRES_PASSWORD=ihr-sicheres-db-passwort

# Domain für den Zugriff
DOMAIN=ihre-domain.de
ALLOWED_HOSTS=ihre-domain.de,localhost,127.0.0.1

# =============================================================================
# OPTIONAL - Nach Bedarf anpassen
# =============================================================================

# Datenbank
POSTGRES_DB=flvs
POSTGRES_USER=flvs

# E-Mail (für Benachrichtigungen)
EMAIL_HOST=smtp.ihr-provider.de
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ihr-email@beispiel.de
EMAIL_HOST_PASSWORD=ihr-email-passwort
DEFAULT_FROM_EMAIL=noreply@ihre-domain.de

# Ports (Standard: 80/443)
HTTP_PORT=80
HTTPS_PORT=443
```

### 3. Verzeichnisse erstellen

```bash
# Backup-Verzeichnis erstellen
mkdir -p docker/backup
mkdir -p docker/certbot/conf
mkdir -p docker/certbot/www

# Berechtigungen setzen
chmod +x docker/scripts/*.sh
```

### 4. Container bauen und starten

```bash
# Images bauen
docker compose build

# Container im Hintergrund starten
docker compose up -d

# Status prüfen
docker compose ps
```

### 5. Datenbank initialisieren

```bash
# Migrations ausführen
docker compose exec web python manage.py migrate

# Statische Dateien sammeln
docker compose exec web python manage.py collectstatic --noinput

# Superuser erstellen
docker compose exec web python manage.py createsuperuser
```

### 6. Installation prüfen

```bash
# Container-Status
docker compose ps

# Logs prüfen
docker compose logs web

# Health-Check
curl http://localhost:8000/health/
```

---

## SSL/HTTPS einrichten (Empfohlen)

### Option A: Let's Encrypt mit Certbot

```bash
# Domain in .env anpassen
DOMAIN=ihre-domain.de

# Init-Script für SSL ausführen
./docker/scripts/init-ssl.sh

# Certbot-Container mit SSL-Profil starten
docker compose --profile ssl up -d certbot
```

### Option B: Eigenes Zertifikat

```bash
# Zertifikate in den Certbot-Ordner kopieren
cp ihr-zertifikat.pem docker/certbot/conf/live/ihre-domain.de/fullchain.pem
cp ihr-privater-key.pem docker/certbot/conf/live/ihre-domain.de/privkey.pem

# Nginx neu laden
docker compose restart nginx
```

---

## Zugriff

Nach erfolgreicher Installation:

| Dienst | URL |
|--------|-----|
| Web-Anwendung | http://localhost/ oder https://ihre-domain.de/ |
| Admin-Interface | http://localhost/admin/ |

---

## Container-Verwaltung

### Basis-Befehle

```bash
# Alle Container starten
docker compose up -d

# Alle Container stoppen
docker compose down

# Container neu starten
docker compose restart

# Logs anzeigen (alle)
docker compose logs -f

# Logs für einzelnen Service
docker compose logs -f web
docker compose logs -f celery-worker
```

### Django Management Commands

```bash
# Shell öffnen
docker compose exec web python manage.py shell

# Migrations erstellen
docker compose exec web python manage.py makemigrations

# Migrations anwenden
docker compose exec web python manage.py migrate

# Statische Dateien sammeln
docker compose exec web python manage.py collectstatic --noinput

# Passwort ändern
docker compose exec web python manage.py changepassword admin

# Tests ausführen
docker compose exec web python manage.py test
```

### Datenbank-Zugriff

```bash
# PostgreSQL Shell
docker compose exec db psql -U flvs -d flvs

# Datenbank-Backup
docker compose exec db pg_dump -U flvs flvs > backup_$(date +%Y%m%d).sql

# Datenbank wiederherstellen
cat backup.sql | docker compose exec -T db psql -U flvs -d flvs
```

---

## Updates

### Code-Update vom Repository

```bash
cd /opt/flvs

# Neueste Änderungen holen
git pull origin main

# Images neu bauen
docker compose build

# Container neu starten
docker compose up -d

# Migrations ausführen (falls neue vorhanden)
docker compose exec web python manage.py migrate

# Statische Dateien aktualisieren
docker compose exec web python manage.py collectstatic --noinput
```

---

## Backup & Restore

### Automatisches Backup aktivieren

```bash
# Backup-Profil starten
docker compose --profile backup up -d backup
```

### Manuelles Backup

```bash
# Datenbank
docker compose exec db pg_dump -U flvs flvs > backup/db_$(date +%Y%m%d_%H%M%S).sql

# Media-Dateien
docker compose exec web tar -czf /app/media_backup.tar.gz /app/media
docker cp flvs-web:/app/media_backup.tar.gz backup/media_$(date +%Y%m%d).tar.gz

# Vollständiges Backup (Datenbank + Media)
./docker/scripts/backup.sh
```

### Restore

```bash
# Datenbank wiederherstellen
cat backup/db_backup.sql | docker compose exec -T db psql -U flvs -d flvs

# Media-Dateien wiederherstellen
docker cp backup/media_backup.tar.gz flvs-web:/app/
docker compose exec web tar -xzf /app/media_backup.tar.gz -C /
```

---

## Troubleshooting

### Container startet nicht

```bash
# Detaillierte Logs anzeigen
docker compose logs web

# Container-Status prüfen
docker compose ps -a

# Neustart aller Container
docker compose down
docker compose up -d
```

### Datenbank-Verbindungsfehler

```bash
# Datenbank-Container prüfen
docker compose logs db

# Datenbank-Verbindung testen
docker compose exec web python -c "import django; django.setup(); from django.db import connection; connection.ensure_connection(); print('OK')"
```

### Permission-Fehler

```bash
# Berechtigungen für Volumes prüfen
docker compose exec web ls -la /app/

# Berechtigungen korrigieren
docker compose exec web chown -R flvs:flvs /app/media /app/logs
```

### Port bereits belegt

```bash
# Welcher Prozess nutzt Port 80?
sudo lsof -i :80

# Alternative Ports in .env setzen
HTTP_PORT=8080
HTTPS_PORT=8443
```

### Container neu bauen (bei Problemen)

```bash
# Kompletter Neuaufbau ohne Cache
docker compose down -v
docker compose build --no-cache
docker compose up -d

# Danach Datenbank neu initialisieren!
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                        Host-System                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Docker Network                      │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │
│  │  │  Nginx  │  │   Web   │  │  Redis  │            │   │
│  │  │  :80    │─▶│  :8000  │◀─│  :6379  │            │   │
│  │  │  :443   │  │ Django  │  │  Cache  │            │   │
│  │  └─────────┘  └────┬────┘  └─────────┘            │   │
│  │                    │                               │   │
│  │       ┌────────────┼────────────┐                 │   │
│  │       │            │            │                 │   │
│  │  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐          │   │
│  │  │ Celery  │  │ Celery  │  │ Postgres│          │   │
│  │  │ Worker  │  │  Beat   │  │  :5432  │          │   │
│  │  └─────────┘  └─────────┘  └─────────┘          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Volumes: postgres_data, redis_data, static_files,         │
│           media_files, log_files                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Container-Übersicht

| Container | Beschreibung | Port |
|-----------|--------------|------|
| flvs-web | Django-Anwendung mit Gunicorn | 8000 |
| flvs-db | PostgreSQL Datenbank | 5432 |
| flvs-redis | Redis Cache & Message Broker | 6379 |
| flvs-nginx | Reverse Proxy & Static Files | 80, 443 |
| flvs-celery-worker | Background Tasks | - |
| flvs-celery-beat | Scheduled Tasks | - |
| flvs-certbot | SSL-Zertifikat-Verwaltung | - |
| flvs-backup | Automatische Backups | - |

---

## Sicherheitshinweise

1. **SECRET_KEY**: Immer einen sicheren, zufälligen Key verwenden
2. **Passwörter**: Starke Passwörter für Datenbank und Admin
3. **HTTPS**: In Produktion immer SSL/TLS aktivieren
4. **Firewall**: Nur Ports 80/443 nach außen freigeben
5. **Updates**: Regelmäßig `git pull` und `docker compose build`
6. **Backups**: Automatische Backups aktivieren und testen

---

## Support

- **Repository**: https://github.com/MLeprich/fwlv
- **Issues**: https://github.com/MLeprich/fwlv/issues

---

*Erstellt: Dezember 2024*
*Django Version: 5.0.14*
*Python Version: 3.12*
