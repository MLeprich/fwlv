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
sudo git clone https://github.com/MLeprich/fwlv.git /opt/flvs
cd /opt/flvs
./install.sh
```

Ausführliche Anleitung: [docs/DOCKER_INSTALLATION.md](docs/DOCKER_INSTALLATION.md)

> **Warum `/opt/flvs`?** Docker Compose leitet den Projektnamen aus dem Verzeichnisnamen
> ab. Wer im Home-Verzeichnis installiert und später aus einem anderen Pfad heraus
> `docker compose` aufruft, startet einen **zweiten, leeren Stack** – die Datenbank scheint
> verschwunden. Deshalb ein festes Verzeichnis, und `/opt` ist dafür der vorgesehene Ort.

### Option B: Ziel-VM ohne Internetzugang (Air-Gap)

Auf einer abgeschotteten VM kann **nicht gebaut** werden – `docker compose build` bräuchte
Docker Hub, PyPI und die Debian-Repos. Die Images werden deshalb vorab auf einer Maschine
**mit** Internet gebaut und als Bundle übertragen:

```bash
# 1. Auf einer Maschine MIT Internet:
./docker/scripts/build-offline-bundle.sh      # erzeugt flvs-images.tar (~400 MB)

# 2. Repository UND flvs-images.tar auf die VM kopieren, beides nach /opt/flvs

# 3. Auf der Ziel-VM – hier wird NICHT gebaut:
cd /opt/flvs && ./install.sh --offline
```

Der Offline-Modus greift an keiner Stelle ins Netz: kein Klon, kein `apt`, kein Build.
Details und Fallstricke: [docs/DOCKER_INSTALLATION.md](docs/DOCKER_INSTALLATION.md#installation-ohne-internet-air-gap--stadt-vm)

### Option C: Manuelle Installation

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

## Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| [docs/DOCKER_INSTALLATION.md](docs/DOCKER_INSTALLATION.md) | Docker Compose Installation |
| [SBOM.md](SBOM.md) | Software Bill of Materials |

## Lizenz

Proprietär
