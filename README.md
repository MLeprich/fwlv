# Feuerwehr Lagerverwaltungssystem (FLVS)

Ein Lagerverwaltungssystem für Feuerwehr und Katastrophenschutz.

## Features

- **Lagermodule:** Medizin, Kleiderkammer, Magazin, Werkstatt, Ausrüstung, Höhenrettung, Tauchen, IT-Hardware
- **Prozesse:** Fahrzeugübernahme, Bestellwesen, Inventur, Dokumentenmanagement
- **Sicherheit:** BTM-Vier-Augen-Prinzip, Rollenbasierte Berechtigungen, Audit-Trail
- **Dashboard:** KPIs, Reports, Info-Monitore

## Technologie

- Python 3.12 / Django 5.0
- PostgreSQL / Redis
- HTMX / Tailwind CSS

## Installation

```bash
# Repository klonen
git clone https://github.com/MLeprich/fwlv.git
cd fwlv

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Konfiguration
cp .env.example .env
nano .env  # SECRET_KEY und ALLOWED_HOSTS anpassen

# Datenbank
python manage.py migrate
python manage.py createsuperuser

# Server starten
python manage.py runserver 0.0.0.0:8000
```

## Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| [INSTALL_DOCKER.md](INSTALL_DOCKER.md) | Container-Installation |
| [SBOM.md](SBOM.md) | Software Bill of Materials |
| [CLAUDE.md](CLAUDE.md) | Projektdokumentation |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Server-Konfiguration |

## Lizenz

Proprietär
