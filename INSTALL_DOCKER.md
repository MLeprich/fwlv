# FLVS - Container Installation

Kurzanleitung zur manuellen Einrichtung in einem Linux-Container.

## Voraussetzungen

- Linux Container (Ubuntu 22.04+ / Debian 12+)
- Python 3.12+
- PostgreSQL 15+ (oder SQLite für Tests)
- Redis 7+
- Git

## Installation

```bash
# 1. Repository klonen
git clone https://github.com/MLeprich/fwlv.git /var/www/flvs
cd /var/www/flvs

# 2. Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# 4. Umgebungsvariablen konfigurieren
cp .env.example .env
nano .env  # SECRET_KEY und ALLOWED_HOSTS anpassen

# 5. Verzeichnisse erstellen
mkdir -p logs media staticfiles

# 6. Datenbank initialisieren
python manage.py migrate

# 7. Statische Dateien sammeln
python manage.py collectstatic --noinput

# 8. Superuser erstellen
python manage.py createsuperuser

# 9. Server starten (Entwicklung)
python manage.py runserver 0.0.0.0:8000

# Oder mit Gunicorn (Produktion)
gunicorn --bind 0.0.0.0:8000 --workers 3 flvs_project.wsgi:application
```

## Wichtige .env Einstellungen

```bash
SECRET_KEY=ihr-sicherer-key          # python -c "import secrets; print(secrets.token_urlsafe(50))"
DEBUG=False
ALLOWED_HOSTS=ihre-domain.de,localhost
DATABASE_URL=postgres://user:pass@localhost:5432/flvs  # Optional, sonst SQLite
```

## Nach Code-Updates

```bash
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
# Server neu starten
```
