# FLVS - Docker Installation

Anleitung zur Installation des Feuerwehr Lagerverwaltungssystems (FLVS) mit Docker Compose in einer VM-Container-Umgebung.

---

## Voraussetzungen

### Systemanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 2 Cores | 4 Cores |
| RAM | 4 GB | 8 GB |
| Speicher | 20 GB | 50 GB |
| OS | Ubuntu 22.04+ / Debian 12+ | Ubuntu 24.04 LTS |

### Software-Voraussetzungen

- Docker Engine 24.0+
- Docker Compose v2.20+
- Git

```bash
# Docker installieren (falls noch nicht vorhanden)
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Docker Compose ist in aktuellen Docker-Versionen integriert
docker compose version
```

---

## Schnellstart

### 1. Repository klonen

```bash
git clone https://github.com/MLeprich/fwlv.git /opt/flvs
cd /opt/flvs
```

### 2. Umgebungsvariablen konfigurieren

```bash
# Beispiel-Konfiguration kopieren
cp .env.example .env

# Konfiguration anpassen
nano .env
```

**Wichtige Einstellungen in `.env`:**

```bash
# PFLICHT: Sicheren Secret Key generieren
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# PFLICHT: Datenbank-Passwort setzen
POSTGRES_PASSWORD=IhrSicheresPasswort123!

# Domain anpassen (für SSL und ALLOWED_HOSTS)
DOMAIN=flvs.ihre-stadt.de
ALLOWED_HOSTS=flvs.ihre-stadt.de,localhost

# Optional: Superuser automatisch erstellen
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=IhrAdminPasswort123!
SUPERUSER_EMAIL=admin@ihre-stadt.de
```

### 3. Verzeichnisse erstellen

```bash
# Backup- und SSL-Verzeichnisse anlegen
mkdir -p docker/backup
mkdir -p docker/certbot/conf
mkdir -p docker/certbot/www
```

### 4. Container starten

```bash
# Alle Services starten
docker compose up -d

# Logs verfolgen (optional)
docker compose logs -f
```

### 5. Status prüfen

```bash
# Container-Status
docker compose ps

# Health-Check
curl http://localhost/health/
```

---

## Zugriff

Nach erfolgreichem Start ist die Anwendung erreichbar unter:

- **Web-Oberfläche:** http://localhost/ (oder http://ihre-domain.de/)
- **Admin-Bereich:** http://localhost/admin/

**Standard-Login (wenn CREATE_SUPERUSER=true):**
- Benutzer: `admin`
- Passwort: In `.env` definiert oder `changeme123`

---

## SSL/HTTPS aktivieren (Produktion)

### Option A: Let's Encrypt (empfohlen)

```bash
# SSL-Zertifikat anfordern
./docker/scripts/init-ssl.sh ihre-domain.de admin@ihre-domain.de

# HTTPS in Nginx aktivieren
nano docker/nginx/conf.d/default.conf
# Auskommentierung des HTTPS-Blocks entfernen
# HTTP-Redirect aktivieren

# Nginx neu laden
docker compose exec nginx nginx -s reload
```

### Option B: Eigenes Zertifikat

```bash
# Zertifikate in das richtige Verzeichnis kopieren
mkdir -p docker/certbot/conf/live/ihre-domain.de/
cp fullchain.pem docker/certbot/conf/live/ihre-domain.de/
cp privkey.pem docker/certbot/conf/live/ihre-domain.de/

# HTTPS in Nginx aktivieren (wie oben)
```

---

## Backup-System aktivieren

```bash
# Backup-Profile aktivieren
docker compose --profile backup up -d

# Manuelles Backup erstellen
docker compose exec backup /backup.sh

# Backups anzeigen
ls -la docker/backup/
```

**Automatisches Backup:** Der Backup-Container führt täglich Backups durch und löscht alte Backups nach 30 Tagen (konfigurierbar via `BACKUP_RETENTION_DAYS`).

---

## Wartung & Administration

### Container-Verwaltung

```bash
# Status aller Container
docker compose ps

# Logs anzeigen
docker compose logs -f web
docker compose logs -f celery-worker

# Container neu starten
docker compose restart web

# Alle Container stoppen
docker compose down

# Alle Container stoppen und Volumes löschen (ACHTUNG: Datenverlust!)
docker compose down -v
```

### Django-Befehle ausführen

```bash
# Django Shell
docker compose exec web python manage.py shell

# Migrationen manuell ausführen
docker compose exec web python manage.py migrate

# Superuser erstellen
docker compose exec web python manage.py createsuperuser

# Static Files sammeln
docker compose exec web python manage.py collectstatic --noinput
```

### Datenbank-Zugriff

```bash
# PostgreSQL Shell
docker compose exec db psql -U flvs -d flvs

# Datenbank-Dump erstellen
docker compose exec db pg_dump -U flvs flvs > backup.sql

# Datenbank wiederherstellen
cat backup.sql | docker compose exec -T db psql -U flvs flvs
```

---

## Updates

### Schnelles Update mit Script

```bash
# Automatisches Update mit Backup
./docker/scripts/update.sh
```

### Manuelles Anwendungs-Update

```bash
cd /opt/flvs

# Änderungen holen
git pull origin main

# Images neu bauen
docker compose build

# Container mit neuen Images starten
docker compose up -d

# Logs prüfen
docker compose logs -f web
```

### Docker-Images aktualisieren

```bash
# Basis-Images aktualisieren
docker compose pull

# Container neu starten
docker compose up -d
```

---

## Verfügbare Skripte

Im Verzeichnis `docker/scripts/` befinden sich folgende Hilfsskripte:

| Skript | Beschreibung | Verwendung |
|--------|--------------|------------|
| `entrypoint.sh` | Container-Startskript (automatisch) | Wird vom Container ausgeführt |
| `init-database.sh` | Datenbank vollständig initialisieren | `docker compose exec web ./docker/scripts/init-database.sh` |
| `init-ssl.sh` | SSL-Zertifikat mit Let's Encrypt | `./docker/scripts/init-ssl.sh domain.de email@domain.de` |
| `backup.sh` | Manuelles Datenbank-Backup | `docker compose exec backup /backup.sh` |
| `restore-backup.sh` | Backup wiederherstellen | `docker compose exec web ./docker/scripts/restore-backup.sh backup_file.sql.gz` |
| `update.sh` | System aktualisieren | `./docker/scripts/update.sh` |

### Datenbank-Initialisierung

Das `init-database.sh` Skript führt folgende Schritte aus:

1. Datenbank-Migrationen
2. Static Files sammeln
3. Basis-Permissions und Rollen einrichten
4. Modul-spezifische Permissions konfigurieren
5. Optional: Superuser erstellen

```bash
# Mit Superuser-Erstellung
CREATE_SUPERUSER=true docker compose exec web ./docker/scripts/init-database.sh

# Oder mit Flag
docker compose exec web ./docker/scripts/init-database.sh --create-superuser
```

### One-Click Installation

Für neue Installationen auf einer frischen VM:

```bash
# Herunterladen und ausführen
curl -fsSL https://raw.githubusercontent.com/MLeprich/fwlv/main/install.sh | bash

# Oder mit Optionen
./install.sh --domain flvs.meine-feuerwehr.de --email admin@meine-feuerwehr.de
```

---

## Troubleshooting

### Container startet nicht

```bash
# Logs prüfen
docker compose logs web

# Häufige Ursachen:
# - SECRET_KEY nicht gesetzt
# - POSTGRES_PASSWORD nicht gesetzt
# - Port bereits belegt
```

### Datenbank-Verbindung fehlgeschlagen

```bash
# DB-Container Status prüfen
docker compose ps db
docker compose logs db

# Manuell verbinden testen
docker compose exec web python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
```

### Migrationen fehlgeschlagen

```bash
# Migration-Status prüfen
docker compose exec web python manage.py showmigrations

# Migrationen manuell ausführen
docker compose exec web python manage.py migrate --run-syncdb
```

### Static Files fehlen

```bash
# Static Files neu sammeln
docker compose exec web python manage.py collectstatic --noinput --clear

# Nginx neu laden
docker compose exec nginx nginx -s reload
```

### Speicherplatz prüfen

```bash
# Docker-Speicherverbrauch
docker system df

# Ungenutzte Ressourcen bereinigen
docker system prune -a
```

---

## Konfigurationsreferenz

### Alle Umgebungsvariablen

| Variable | Pflicht | Standard | Beschreibung |
|----------|---------|----------|--------------|
| `SECRET_KEY` | Ja | - | Django Secret Key |
| `POSTGRES_PASSWORD` | Ja | - | Datenbank-Passwort |
| `POSTGRES_DB` | Nein | `flvs` | Datenbankname |
| `POSTGRES_USER` | Nein | `flvs` | Datenbank-Benutzer |
| `DEBUG` | Nein | `False` | Debug-Modus |
| `ALLOWED_HOSTS` | Nein | `localhost,127.0.0.1` | Erlaubte Hosts |
| `DOMAIN` | Nein | `localhost` | Domain für Nginx |
| `HTTP_PORT` | Nein | `80` | HTTP-Port |
| `HTTPS_PORT` | Nein | `443` | HTTPS-Port |
| `CREATE_SUPERUSER` | Nein | `false` | Auto-Superuser erstellen |
| `SUPERUSER_USERNAME` | Nein | `admin` | Superuser-Name |
| `SUPERUSER_PASSWORD` | Nein | `changeme123` | Superuser-Passwort |
| `SUPERUSER_EMAIL` | Nein | `admin@flvs.local` | Superuser-Email |
| `EMAIL_HOST` | Nein | - | SMTP-Server |
| `EMAIL_PORT` | Nein | `587` | SMTP-Port |
| `EMAIL_HOST_USER` | Nein | - | SMTP-Benutzer |
| `EMAIL_HOST_PASSWORD` | Nein | - | SMTP-Passwort |
| `EMAIL_USE_TLS` | Nein | `True` | TLS verwenden |
| `BACKUP_RETENTION_DAYS` | Nein | `30` | Backup-Aufbewahrung (Tage) |

### Docker Compose Profile

| Profil | Beschreibung | Aktivierung |
|--------|--------------|-------------|
| (Standard) | Web, DB, Redis, Nginx, Celery | `docker compose up -d` |
| `ssl` | + Certbot für SSL | `docker compose --profile ssl up -d` |
| `backup` | + Automatische Backups | `docker compose --profile backup up -d` |

---

## Architektur

```
                    ┌─────────────┐
                    │   Nginx     │ :80/:443
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Static  │ │  Media   │ │   Web    │
        │  Files   │ │  Files   │ │ (Django/ │
        │          │ │          │ │ Gunicorn)│
        └──────────┘ └──────────┘ └────┬─────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
              ┌──────────┐      ┌──────────┐      ┌──────────┐
              │PostgreSQL│      │  Redis   │      │  Celery  │
              │   (DB)   │      │ (Cache)  │      │ (Worker) │
              └──────────┘      └──────────┘      └──────────┘
```

---

## Sicherheitshinweise

1. **Passwörter ändern:** Alle Standard-Passwörter in `.env` durch sichere Passwörter ersetzen
2. **SECRET_KEY:** Niemals den Beispiel-Key verwenden, immer neu generieren
3. **DEBUG=False:** In Produktion immer deaktiviert lassen
4. **HTTPS:** Für Produktion immer SSL aktivieren
5. **Firewall:** Nur Ports 80/443 nach außen freigeben
6. **Updates:** Regelmäßig Docker-Images und Anwendung aktualisieren

---

## Support

Bei Problemen:

1. Logs prüfen: `docker compose logs`
2. Container-Status: `docker compose ps`
3. GitHub Issues: https://github.com/MLeprich/fwlv/issues

---

*Letzte Aktualisierung: Februar 2026*
