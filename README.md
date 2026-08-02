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
Docker Hub, PyPI und die Debian-Repos. **Das ist auch nicht nötig:** für jede Version wird
ein fertiges Image-Bundle als GitHub-Release bereitgestellt.

```bash
sudo git clone https://github.com/MLeprich/fwlv.git /opt/flvs
cd /opt/flvs
git checkout v1.0.0          # der Tag des Releases (siehe Releases-Seite)

# Fertiges Bundle laden (~400 MB) – NICHT selbst bauen
curl -L -o flvs-images.tar \
  https://github.com/MLeprich/fwlv/releases/latest/download/flvs-images.tar

./install.sh --offline
```

Der Offline-Modus greift an keiner Stelle ins Netz: kein Klon, kein `apt`, kein Build.
Kommt die VM nicht einmal an GitHub, werden Repository und Bundle per `scp`/USB kopiert.

> **Updates:** Der Code ist als Bind-Mount (`.:/app`) eingebunden. Code-, Template- und
> Migrations-Änderungen kommen daher per `git pull` + `./docker/scripts/update-offline.sh`
> auf die VM – **ohne** Rebuild und **ohne** neues Bundle. Ein neues Image-Bundle ist nur
> nötig, wenn sich Abhängigkeiten ändern (`requirements.txt`/`Dockerfile`).

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
