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

### Option A: Docker (empfohlen)

```bash
git clone https://github.com/MLeprich/fwlv.git
cd fwlv

cp .env.example .env
nano .env  # SECRET_KEY und POSTGRES_PASSWORD setzen

docker compose up -d
```

Ausführliche Anleitung: [docs/DOCKER_INSTALLATION.md](docs/DOCKER_INSTALLATION.md)

### Option B: Manuelle Installation

```bash
git clone https://github.com/MLeprich/fwlv.git
cd fwlv

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env  # SECRET_KEY und ALLOWED_HOSTS anpassen

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

Ausführliche Anleitung: [INSTALL_DOCKER.md](INSTALL_DOCKER.md)

## Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| [docs/DOCKER_INSTALLATION.md](docs/DOCKER_INSTALLATION.md) | Docker Compose Installation |
| [INSTALL_DOCKER.md](INSTALL_DOCKER.md) | Manuelle Container-Installation |
| [SBOM.md](SBOM.md) | Software Bill of Materials |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Server-Konfiguration |

## Lizenz

Proprietär
