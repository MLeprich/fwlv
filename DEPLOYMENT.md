# FLVS - Deployment-Dokumentation

## ✅ Production-Deployment abgeschlossen

Das Feuerwehr Lagerverwaltungssystem (FLVS) ist jetzt unter **https://lager.resqware.de** erreichbar!

---

## Server-Konfiguration

### 1. Gunicorn Service

**Service-Datei:** `/etc/systemd/system/flvs.service`

```bash
# Service starten
sudo systemctl start flvs

# Service stoppen
sudo systemctl stop flvs

# Service neu starten
sudo systemctl restart flvs

# Status prüfen
sudo systemctl status flvs

# Logs ansehen
sudo journalctl -u flvs -f
```

**Gunicorn läuft auf:** `127.0.0.1:8002`

### 2. Nginx-Konfiguration

**Config-Datei:** `/etc/nginx/sites-available/lager.resqware.de`

```bash
# Nginx-Config testen
sudo nginx -t

# Nginx neu laden
sudo systemctl reload nginx

# Nginx neu starten
sudo systemctl restart nginx
```

### 3. SSL/TLS

- ✅ Let's Encrypt SSL-Zertifikat aktiv
- ✅ HTTPS erzwungen (HTTP → HTTPS Redirect)
- ✅ Certbot managed

```bash
# Zertifikat erneuern (automatisch via Cronjob)
sudo certbot renew

# Zertifikat-Status prüfen
sudo certbot certificates
```

---

## Wichtige Pfade

| Beschreibung | Pfad |
|--------------|------|
| Projekt-Root | `/var/www/lager.resqware.de` |
| Virtual Environment | `/var/www/lager.resqware.de/venv` |
| Static Files | `/var/www/lager.resqware.de/staticfiles` |
| Media Files | `/var/www/lager.resqware.de/media` |
| Logs | `/var/www/lager.resqware.de/logs` |
| Datenbank (Dev) | `/var/www/lager.resqware.de/db.sqlite3` |
| Environment | `/var/www/lager.resqware.de/.env` |

---

## Log-Dateien

```bash
# Gunicorn Access Log
tail -f /var/www/lager.resqware.de/logs/gunicorn-access.log

# Gunicorn Error Log
tail -f /var/www/lager.resqware.de/logs/gunicorn-error.log

# Django Application Log
tail -f /var/www/lager.resqware.de/logs/flvs.log

# Nginx Access Log
sudo tail -f /var/log/nginx/access.log

# Nginx Error Log
sudo tail -f /var/log/nginx/error.log
```

---

## Management Commands

Alle Commands müssen mit aktiviertem Virtual Environment ausgeführt werden:

```bash
cd /var/www/lager.resqware.de
source venv/bin/activate

# Migrations
python manage.py makemigrations
python manage.py migrate

# Static Files sammeln (nach Code-Änderungen)
python manage.py collectstatic --noinput

# Superuser erstellen
python manage.py createsuperuser

# Shell öffnen
python manage.py shell

# Tests ausführen
python manage.py test
```

---

## Code-Updates

Nach Code-Änderungen:

```bash
cd /var/www/lager.resqware.de
source venv/bin/activate

# 1. Git Pull (wenn verwendet)
git pull origin main

# 2. Requirements aktualisieren (falls geändert)
pip install -r requirements.txt

# 3. Migrations
python manage.py migrate

# 4. Static Files sammeln
python manage.py collectstatic --noinput

# 5. Gunicorn neu starten
sudo systemctl restart flvs
```

---

## Zugriff

### URLs

- **Website:** https://lager.resqware.de/
- **Admin-Interface:** https://lager.resqware.de/admin/

### Admin-Credentials (Standard)

- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@flvs.local`

⚠️ **WICHTIG:** Passwort in Production ändern!

```bash
source venv/bin/activate
python manage.py changepassword admin
```

---

## Security Checklist für Production

### Noch zu erledigen:

- [ ] Admin-Passwort ändern
- [ ] `SECRET_KEY` in `.env` durch sicheren Wert ersetzen
- [ ] `DEBUG=False` in `.env` setzen
- [ ] PostgreSQL statt SQLite konfigurieren
- [ ] Backup-Strategie implementieren
- [ ] 2FA für kritische Benutzer aktivieren
- [ ] CSRF und Session-Cookies secure setzen

### Bereits erledigt:

- [x] SSL/TLS aktiv
- [x] HTTPS erzwungen
- [x] Allowed Hosts konfiguriert
- [x] Gunicorn Service konfiguriert
- [x] Nginx Reverse Proxy konfiguriert
- [x] Static/Media Files korrekt served

---

## Troubleshooting

### Service startet nicht

```bash
# Logs checken
sudo journalctl -u flvs -n 50

# Permissions prüfen
ls -la /var/www/lager.resqware.de

# Virtual Environment prüfen
source venv/bin/activate
python manage.py check
```

### 500 Server Error

```bash
# Django Logs checken
tail -100 /var/www/lager.resqware.de/logs/gunicorn-error.log
tail -100 /var/www/lager.resqware.de/logs/flvs.log

# Debug mode temporär aktivieren (nur zum Debuggen!)
# In .env: DEBUG=True
sudo systemctl restart flvs
```

### Static Files nicht geladen

```bash
# Static Files neu sammeln
source venv/bin/activate
python manage.py collectstatic --noinput

# Permissions prüfen
ls -la /var/www/lager.resqware.de/staticfiles

# Nginx Config prüfen
sudo nginx -t
```

---

## Backup & Recovery

### Manuelles Backup

```bash
# Datenbank (SQLite)
cp /var/www/lager.resqware.de/db.sqlite3 ~/backup/db-$(date +%Y%m%d).sqlite3

# Media Files
tar -czf ~/backup/media-$(date +%Y%m%d).tar.gz /var/www/lager.resqware.de/media

# Komplettes Projekt
tar -czf ~/backup/flvs-$(date +%Y%m%d).tar.gz /var/www/lager.resqware.de \
  --exclude=venv --exclude=staticfiles --exclude=__pycache__
```

### PostgreSQL Backup (wenn konfiguriert)

```bash
pg_dump -U flvs_user flvs > ~/backup/flvs-$(date +%Y%m%d).sql
```

---

## Performance Monitoring

```bash
# Gunicorn Worker Status
sudo systemctl status flvs

# Ressourcen-Verbrauch
top -p $(pgrep -f "gunicorn.*flvs")

# Disk Usage
du -sh /var/www/lager.resqware.de/*

# Logs Size
du -sh /var/www/lager.resqware.de/logs/*
```

---

## Kontakt & Support

- **Projekt:** FLVS - Feuerwehr Lagerverwaltungssystem
- **Domain:** https://lager.resqware.de
- **Server:** Ubuntu Server (lager.resqware.de)
- **Django Version:** 5.0.14
- **Python Version:** 3.12

---

*Erstellt am: 2025-10-03*
*Status: Production Ready*
