# FLVS - Docker Installation

Anleitung zur Installation des Feuerwehr Lagerverwaltungssystems (FLVS) mit Docker Compose in einer VM-Container-Umgebung.

---

## Schnellste Installation (One-Click)

Für eine neue Installation auf einer frischen VM (Ubuntu/Debian):

```bash
# Alles in einem Befehl - installiert Docker, klont Repository, konfiguriert und startet
curl -fsSL https://raw.githubusercontent.com/MLeprich/fwlv/main/install.sh | bash
```

**Mit eigener Domain und E-Mail:**

```bash
# Herunterladen
curl -fsSL https://raw.githubusercontent.com/MLeprich/fwlv/main/install.sh -o install.sh
chmod +x install.sh

# Installation mit Parametern
./install.sh --domain flvs.meine-feuerwehr.de --email admin@meine-feuerwehr.de
```

Nach ca. 5-10 Minuten ist die Anwendung unter `http://ihre-domain/` erreichbar. Die Login-Daten werden am Ende angezeigt und in `/opt/flvs/.credentials` gespeichert.

### install.sh Optionen

| Option | Beschreibung | Beispiel |
|--------|--------------|----------|
| `--domain` | Domain für die Installation | `--domain flvs.feuerwehr.de` |
| `--email` | Admin E-Mail-Adresse | `--email admin@feuerwehr.de` |
| `--password` | Admin-Passwort (sonst generiert) | `--password MeinPasswort123` |
| `--install-dir` | Installationsverzeichnis (Standard `/opt/flvs`) | `--install-dir /opt/flvs` |
| `--skip-docker-install` | Docker-Installation überspringen | `--skip-docker-install` |
| **`--offline`** | **Für VMs ohne Internet: nicht klonen, nicht bauen, Images aus dem Bundle laden** | `--offline` |
| `--image-bundle` | Pfad zum Bundle (Standard `<install-dir>/flvs-images.tar`) | `--image-bundle /tmp/flvs-images.tar` |

### Was das Skript automatisch macht

1. Systemvoraussetzungen prüfen (RAM, Speicher, OS)
2. Erreichbarkeit von GitHub, Docker Hub, PyPI und den Debian-Repos prüfen –
   fehlt eines davon, bricht es ab und verweist auf `--offline` (entfällt im Offline-Modus)
3. Docker installieren (falls nicht vorhanden)
4. Repository nach `/opt/flvs` klonen (im Offline-Modus: vorhandenes verwenden)
5. Sichere Passwörter generieren (SECRET_KEY, DB-Passwort, Admin-Passwort)
6. `.env` Konfiguration erstellen
7. Docker-Container bauen und starten (im Offline-Modus: `docker load` aus dem Bundle)
8. Datenbank migrieren und Permissions einrichten
9. Superuser erstellen
10. Zugangsdaten in `.credentials` speichern

> **Nicht aus dem Installationsverzeichnis heraus starten.** Beim Überschreiben würde sich
> das Skript selbst löschen und danach mit der alten Fassung weiterlaufen – Bash liest aus
> dem gelöschten Inode weiter. Genau so lief auf der Stadt-VM zweimal ein veralteter Stand,
> der `--offline` noch gar nicht kannte. Das Skript bricht heute in diesem Fall ab. Im
> Offline-Modus ist der Aufruf aus `/opt/flvs` dagegen richtig – dort wird ja nichts geklont.

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

## Installation ohne Internet (Air-Gap / Stadt-VM)

### Es sind ZWEI Maschinen im Spiel

Das ist der Punkt, an dem die Installation erfahrungsgemäß scheitert. Die Arbeit teilt
sich auf zwei Rechner auf, und beide haben eine klar getrennte Rolle:

| | Maschine **MIT** Internet | Ziel-VM **OHNE** Internet |
|---|---|---|
| **Rolle** | baut | installiert |
| **Skript** | `build-offline-bundle.sh` | `install.sh --offline` |
| **Ergebnis** | `flvs-images.tar` (ca. 400 MB) | laufende Anwendung |
| **Braucht Netz** | ja (Docker Hub, PyPI, Debian) | **nein** |

> **Auf der Ziel-VM wird NICHT gebaut.** `build-offline-bundle.sh` gehört dort nicht hin:
> es lädt Basis-Images vom Docker Hub und führt `apt`/`pip` im Container aus. Ohne Netz
> kann das nicht funktionieren. Startet man es trotzdem dort, bricht es heute mit einer
> Erklärung ab – früher lief es 30 Sekunden ins Leere und meldete dann nur:
>
> ```
> failed to fetch anonymous token: Get "https://auth.docker.io/token?...": i/o timeout
> ```
>
> Dieselbe Meldung erscheint, wenn man `install.sh` **ohne** `--offline` startet: dann
> baut Compose ebenfalls.

**Ein Proxy hilft hier meist nicht.** Selbst wenn `docker pull` über einen Proxy
funktioniert: Docker BuildKit übernimmt die Proxy-Umgebung **nicht** automatisch, und die
`apt`- und `pip`-Aufrufe *innerhalb* des Builds laufen ins Leere. Der Offline-Weg umgeht
das komplett – er baut ja nicht.

**Zur Laufzeit braucht die Anwendung kein Internet.** Frontend (Tailwind, Alpine.js,
HTMX), Datenbank und Cache sind lokal eingebunden.

---

### Wohin installieren – und warum `/opt/flvs`?

Das Installationsverzeichnis ist **nicht** frei wählbar im Sinne von „egal". Es muss
**ein einziges, festes Verzeichnis** sein, aus dem heraus alles läuft. Der Standard ist
`/opt/flvs`; mit `--install-dir` lässt sich ein anderes wählen – aber dann konsequent
überall dasselbe.

Warum das so wichtig ist:

1. **Docker Compose leitet den Projektnamen aus dem Verzeichnisnamen ab.** In `~/fwlv`
   heißt das Projekt `fwlv`, in `/opt/flvs` heißt es `flvs`. Das sind **zwei getrennte
   Stacks mit getrennten Volumes** (`fwlv_postgres_data` vs. `flvs_postgres_data`). Wer
   im Home-Verzeichnis installiert und später aus `/opt/flvs` heraus `docker compose`
   aufruft, startet einen **zweiten, leeren Stack** – die Datenbank scheint verschwunden.
   Das ist der teuerste Fehler in dieser Anleitung.

2. **Alles hängt relativ am Verzeichnis.** `.env`, `.credentials`, die Backups
   (`docker/backup/`), die Zertifikate (`docker/certbot/`) und die nginx-Konfiguration
   werden als Bind-Mounts eingebunden. Verschiebt man das Verzeichnis später, zeigen die
   Mounts ins Leere.

3. **`install.sh --offline` sucht das Bundle unter `<install-dir>/flvs-images.tar`.**
   Liegt es woanders, muss man es explizit angeben (`--image-bundle`).

4. **`/opt` ist der vorgesehene Ort.** Nach FHS gehört dorthin in sich geschlossene
   Software, die nicht aus der Paketverwaltung der Distribution stammt – genau das ist ein
   Docker-Compose-Stack mit eigener Konfiguration und eigenen Zertifikaten. Ein
   Home-Verzeichnis (`~/fwlv`) ist der falsche Ort: die Container laufen unter root, das
   Backup-Profil und ein Neustart nach Reboot hängen nicht an einem Benutzer-Login, und
   die Zugangsdaten in `.credentials` haben im Home nichts verloren.

---

### Das Bundle muss nicht selbst gebaut werden

Für jede Version wird ein fertiges Bundle als **GitHub-Release** bereitgestellt. Wer
installiert, **baut nicht** – er lädt herunter. Selbst bauen muss nur, wer eine eigene,
noch nicht veröffentlichte Codeversion ausrollen will (siehe „Neues Bundle bereitstellen"
weiter unten).

> **Wichtig: Das Bundle IST die Anwendungsversion.** Der Quellcode wird beim Bauen in das
> Image gebacken (`COPY . .` im Dockerfile), und der Container mountet **keinen** Quellcode
> vom Host. Das geklonte Repository liefert nur die Infrastruktur (`docker-compose.yml`,
> `install.sh`, nginx-Konfiguration).
>
> Daraus folgt: **Ein `git pull` auf der VM aktualisiert die Anwendung nicht.** Wer das Repo
> aktualisiert und sich wundert, warum die neuen Funktionen fehlen, ist genau hier
> hineingelaufen. Repository und Bundle müssen zum **selben Stand** gehören – deshalb wird
> auf der VM der Release-Tag ausgecheckt, zu dem das Bundle gehört.

### 1. Bundle und Repository auf die Ziel-VM bringen

Die VM erreicht GitHub in vielen Netzen auch dann, wenn Docker Hub gesperrt ist (der Proxy
lässt `git`/`https` durch). Dann geht es direkt auf der VM:

```bash
# Repository auf den Stand des Releases bringen
sudo git clone https://github.com/MLeprich/fwlv.git /opt/flvs
cd /opt/flvs
git checkout v1.0.0                    # der Tag des Releases – derselbe wie beim Bundle!

# Fertiges Bundle herunterladen (ca. 400 MB)
curl -L -o flvs-images.tar \
  https://github.com/MLeprich/fwlv/releases/latest/download/flvs-images.tar
```

> `releases/latest/download/…` zeigt immer auf das neueste Release. Soll eine **bestimmte**
> Version installiert werden, den Tag explizit angeben:
> `https://github.com/MLeprich/fwlv/releases/download/v1.0.0/flvs-images.tar`

**Hinter einem Proxy wichtig:** GitHub leitet den Download auf einen **anderen Host** um –
`release-assets.githubusercontent.com`. Eine Freigabe, die nur `github.com` kennt, reicht
also nicht; der `git clone` funktioniert dann zwar, der Asset-Download aber nicht. In dem
Fall entweder den Host mit freigeben lassen oder das Bundle per `scp`/USB übertragen
(siehe unten). Ob es klappt, zeigt ein Test auf der VM:

```bash
curl -sIL https://github.com/MLeprich/fwlv/releases/latest/download/flvs-images.tar \
  | grep -E '^HTTP|^location'
```

**Kommt die VM gar nicht ins Netz** (auch nicht zu GitHub), dann beides von einer anderen
Maschine herüberkopieren – per `scp` oder USB-Stick:

```bash
scp -r fwlv/             root@ziel-vm:/opt/flvs
scp fwlv/flvs-images.tar root@ziel-vm:/opt/flvs/flvs-images.tar
```

Danach muss es auf der VM so aussehen:

```
/opt/flvs/
├── install.sh
├── docker-compose.yml
├── Dockerfile
├── flvs-images.tar      <- das Bundle
└── ...
```

### 2. Auf der Ziel-VM offline installieren

```bash
cd /opt/flvs
./install.sh --offline
```

Der `--offline`-Modus greift an **keiner einzigen Stelle** ins Netz:

- kein `git clone` (verwendet das vorhandene Repository),
- kein `apt-get` (prüft nur, ob `git`, `curl` und `openssl` vorhanden sind),
- kein Build – die Images kommen per `docker load` aus dem Bundle,
- Start mit `docker compose up -d --no-build --pull never`; ein fehlendes Image schlägt
  hart fehl, statt still nachgeladen zu werden.

Docker selbst muss auf der VM **vorinstalliert** sein – der Offline-Modus installiert es
nicht nach.

> Liegt das Bundle woanders: `./install.sh --offline --image-bundle /pfad/zu/flvs-images.tar`

### Prüfen, welcher Skriptstand läuft

`install.sh` zeigt beim Start seinen Pfad und den Commit an:

```
  Skript: /opt/flvs/install.sh
  Stand:  c0e9a73
```

Steht dort ein alter Commit, läuft eine veraltete Fassung – etwa eine, die `--offline`
noch gar nicht kennt. Dann `git pull` und erneut starten.

### Updates auf der VM

Ein Update ist immer **ein neues Bundle** – `git pull` allein ändert nichts an der
laufenden Anwendung, weil der Code im Image steckt (siehe oben).

```bash
cd /opt/flvs

# 1. Repository auf den Stand des neuen Releases bringen
git fetch --tags
git checkout v1.1.0

# 2. Passendes Bundle holen und laden
curl -L -o flvs-images.tar \
  https://github.com/MLeprich/fwlv/releases/download/v1.1.0/flvs-images.tar
docker load -i flvs-images.tar

# 3. Container mit den neuen Images starten (kein Build, kein Registry-Zugriff)
docker compose up -d --no-build --pull never
docker compose exec web python manage.py migrate
```

> Der Tag beim `git checkout` und der Tag des Bundles müssen **derselbe** sein. Sonst
> laufen die Container mit dem Code aus dem Image, während `docker-compose.yml` und die
> nginx-Konfiguration von einem anderen Stand stammen.

---

## Neues Bundle bereitstellen (für Betreuer/Entwickler)

Wer eine neue Version für die abgeschotteten VMs veröffentlicht, macht das **auf einer
Maschine mit Internet**:

```bash
# 1. Auf dem Stand bauen, der veröffentlicht werden soll
git checkout main && git pull
./docker/scripts/build-offline-bundle.sh          # erzeugt flvs-images.tar (~400 MB)

# 2. Version taggen
git tag v1.1.0 && git push origin v1.1.0

# 3. Release anlegen und das Bundle als Asset anhängen
gh release create v1.1.0 flvs-images.tar \
  --title "FLVS v1.1.0" \
  --notes "Offline-Bundle für Air-Gap-Installationen. Auf der Ziel-VM: git checkout v1.1.0 && ./install.sh --offline"
```

Ohne `gh` geht es genauso über die GitHub-Weboberfläche: *Releases → Draft a new release →
Tag wählen → `flvs-images.tar` als Asset hochladen*.

**Die Datei muss exakt `flvs-images.tar` heißen.** Nur dann funktioniert die stabile
Download-URL, auf die diese Anleitung verweist:

```
https://github.com/MLeprich/fwlv/releases/latest/download/flvs-images.tar
```

---

## Betrieb nach der Installation (was offline NICHT geht)

**Zur Laufzeit ist das System offline-fähig:** Frontend (Tailwind, Alpine.js, HTMX),
Datenbank, Cache und alle Anwendungs-Abhängigkeiten sind lokal eingebunden. Es gibt jedoch
**zwei Dinge, die kein Internet mehr haben**:

| Funktion | Auswirkung offline | Empfehlung |
|----------|--------------------|------------|
| **Let's Encrypt SSL** | Auto-Renewal (certbot, alle 12 h) schlägt fehl → Zertifikat läuft nach max. 90 Tagen ab | **Eigenes/internes Zertifikat** verwenden (siehe SSL → Option B), nicht Let's Encrypt |
| **E-Mail-Versand** | Nur möglich, wenn der SMTP-Server intern erreichbar ist | Internen Mailserver/Relay eintragen oder E-Mail deaktiviert lassen |
| Docker Image-Updates | `docker compose pull`/`build` nicht möglich | Neues Bundle extern bauen und per `docker load` einspielen (siehe oben) |

> **Wichtigste Empfehlung:** Auf einer dauerhaft offline betriebenen VM **kein Let's Encrypt**
> verwenden, da die automatische Verlängerung Internet benötigt. Stattdessen ein eigenes
> (ggf. von der internen PKI/Stadt-CA ausgestelltes) Zertifikat über **Option B** einbinden.
> Dieses sollte eine ausreichend lange Laufzeit haben und vor Ablauf manuell in einem
> Wartungsfenster erneuert werden.

> **Hinweis Wiki-Modul:** Eingebettete externe Inhalte (YouTube/Vimeo/Twitter-Embeds) laden
> erst beim Anzeigen aus dem Internet und bleiben offline leer. Das betrifft nur optional vom
> Nutzer eingebettete Medien, keine Kernfunktion.

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

## SSL/HTTPS Konfiguration

### Erstinstallation ohne SSL-Zertifikat

Standardmäßig erwartet die Production-Konfiguration HTTPS. Für die **Erstinstallation ohne SSL-Zertifikat** muss `USE_SSL=false` gesetzt werden:

```bash
# In .env hinzufügen/ändern:
USE_SSL=false
```

Dies deaktiviert:
- HTTPS-Redirect
- Secure Cookies
- HSTS Headers

> **Wichtig:** Nach Einrichtung des SSL-Zertifikats `USE_SSL=true` setzen (oder Zeile entfernen) und Container neu starten!

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
| `USE_SSL` | Nein | `true` | SSL/HTTPS erzwingen (false für Erstinstallation ohne Zertifikat) |
| `CREATE_SUPERUSER` | Nein | `false` | Auto-Superuser erstellen |
| `SUPERUSER_USERNAME` | Nein | `admin` | Superuser-Name |
| `SUPERUSER_PASSWORD` | Nein | `changeme123` | Superuser-Passwort |
| `SUPERUSER_EMAIL` | Nein | `admin@flvs.local` | Superuser-Email |
| `EMAIL_HOST` | Nein | - | SMTP-Server |
| `EMAIL_PORT` | Nein | `587` | SMTP-Port |
| `EMAIL_HOST_USER` | Nein | - | SMTP-Benutzer |
| `EMAIL_HOST_PASSWORD` | Nein | - | SMTP-Passwort |
| `EMAIL_USE_TLS` | Nein | `True` | TLS verwenden |
| `DEFAULT_FROM_EMAIL` | Nein | `noreply@flvs.local` | Absender-Adresse für E-Mails |
| `REDIS_URL` | Nein | `redis://redis:6379/1` | Redis-Verbindung (Cache) |
| `CELERY_BROKER_URL` | Nein | `redis://redis:6379/0` | Celery Broker (Task Queue) |
| `CELERY_RESULT_BACKEND` | Nein | `redis://redis:6379/0` | Celery Result Backend |
| `BACKUP_RETENTION_DAYS` | Nein | `30` | Backup-Aufbewahrung (Tage) |

### Docker Compose Profile

| Profil | Beschreibung | Aktivierung |
|--------|--------------|-------------|
| (Standard) | Web, DB, Redis, Nginx, Celery Worker, Celery Beat | `docker compose up -d` |
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
              ┌────────────────────┬────┴───────┬──────────────┐
              │                    │            │              │
              ▼                    ▼            ▼              ▼
        ┌──────────┐        ┌──────────┐ ┌──────────┐  ┌──────────┐
        │PostgreSQL│        │  Redis   │ │  Celery  │  │  Celery  │
        │   (DB)   │        │ (Cache/  │ │ (Worker) │  │  (Beat)  │
        └──────────┘        │  Broker) │ └──────────┘  └──────────┘
                            └──────────┘
```

---

## Vollständiges Beispiel: Von Null zur laufenden Anwendung

Hier ein komplettes Beispiel für die Installation auf einer frischen Ubuntu 24.04 VM:

```bash
# 1. Als root oder mit sudo einloggen
ssh user@neue-vm.example.de

# 2. System aktualisieren
sudo apt update && sudo apt upgrade -y

# 3. One-Click Installation starten
curl -fsSL https://raw.githubusercontent.com/MLeprich/fwlv/main/install.sh -o install.sh
chmod +x install.sh
./install.sh --domain flvs.meine-feuerwehr.de --email admin@meine-feuerwehr.de

# 4. Warten bis Installation abgeschlossen (ca. 5-10 Minuten)
# Am Ende werden die Login-Daten angezeigt:
#
#   URL:      http://flvs.meine-feuerwehr.de/
#   Admin:    http://flvs.meine-feuerwehr.de/admin/
#
#   Login-Daten:
#   Benutzer: admin
#   Passwort: [generiertes Passwort]

# 5. Optional: SSL aktivieren
cd /opt/flvs
./docker/scripts/init-ssl.sh flvs.meine-feuerwehr.de admin@meine-feuerwehr.de

# 6. USE_SSL aktivieren nach SSL-Einrichtung
sed -i 's/USE_SSL=false/USE_SSL=true/' .env
docker compose up -d

# 7. Fertig! Anwendung ist unter https://flvs.meine-feuerwehr.de/ erreichbar
```

### Nach der Installation

1. **Erstes Login:** Mit den angezeigten Zugangsdaten einloggen
2. **Passwort ändern:** Unbedingt das Admin-Passwort ändern!
3. **Module aktivieren:** Unter Einstellungen → Module die gewünschten Module aktivieren
4. **Benutzer anlegen:** Weitere Benutzer mit entsprechenden Rollen anlegen
5. **Backup aktivieren:** `docker compose --profile backup up -d`

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

*Letzte Aktualisierung: März 2026*
