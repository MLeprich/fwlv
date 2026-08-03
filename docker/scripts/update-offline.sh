#!/bin/bash
# =============================================================================
# FLVS - Offline-Update (ohne Image-Rebuild)
# =============================================================================
# Für abgeschottete Systeme (z.B. Stadt-VM), die zwar `git pull` können, aber
# KEINEN Internetzugang zu Docker Hub / PyPI / apt haben und daher kein Image
# bauen können.
#
# Voraussetzung: In der docker-compose.yml ist der Code als Bind-Mount
# eingebunden (`- .:/app` bei web/celery). Dann reicht für Code-, Template- und
# Migrations-Änderungen ein `git pull` + Container-Neustart – ganz ohne Build.
#
# Für NEUE Abhängigkeiten (requirements.txt / Dockerfile) reicht das NICHT –
# dann muss auf einer Internet-Maschine ein neues Offline-Bundle gebaut werden:
#   ./docker/scripts/build-offline-bundle.sh   (siehe dortige Anleitung)
#
# Verwendung (im Repo-Verzeichnis auf der VM):
#   ./docker/scripts/update-offline.sh
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$INSTALL_DIR"

echo -e "${BLUE}=========================================="
echo "FLVS - Offline-Update (ohne Build)"
echo -e "==========================================${NC}"
echo "Verzeichnis: $INSTALL_DIR"

# ---------------------------------------------------------------------------
# 0) Sicherstellen, dass der Code-Bind-Mount aktiv ist – sonst würde ein
#    Neustart den neuen Code gar nicht laden.
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[1/6]${NC} Prüfe Code-Bind-Mount in docker-compose.yml..."
if ! grep -qE '^\s*-\s*\.:/app\s*$' docker-compose.yml; then
    echo -e "${RED}  ✗ Kein '- .:/app'-Volume gefunden.${NC}"
    echo "    Dieses Skript setzt den Code-Bind-Mount voraus (Option 1)."
    echo "    Ohne ihn muss stattdessen ein neues Image gebaut/geladen werden."
    exit 1
fi
echo -e "${GREEN}  ✓ Bind-Mount vorhanden${NC}"

# ---------------------------------------------------------------------------
# 1) Datenbank-Backup (wie im normalen update.sh)
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[2/6]${NC} Erstelle Datenbank-Backup..."
mkdir -p "$INSTALL_DIR/docker/backup"
BACKUP_FILE="$INSTALL_DIR/docker/backup/pre-update_$(date +%Y%m%d_%H%M%S).sql.gz"
if docker compose exec -T db pg_dump -U "${POSTGRES_USER:-flvs}" "${POSTGRES_DB:-flvs}" | gzip > "$BACKUP_FILE"; then
    echo -e "${GREEN}  ✓ Backup: $BACKUP_FILE${NC}"
else
    echo -e "${RED}  ✗ Backup fehlgeschlagen – Abbruch.${NC}"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# ---------------------------------------------------------------------------
# 2) Neueste Version holen (GitHub ist über den Proxy erreichbar)
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[3/6]${NC} Hole neuesten Stand (git pull)..."
CURRENT=$(git rev-parse --short HEAD)
git pull origin main
NEW=$(git rev-parse --short HEAD)
echo -e "${GREEN}  ✓ $CURRENT → $NEW${NC}"

# ---------------------------------------------------------------------------
# 3) Container neu starten -> lädt den neuen Code aus dem Bind-Mount.
#    Der web-Entrypoint führt dabei automatisch migrate + collectstatic aus.
#    nginx wird mit neu gestartet: löst 'web' beim Start neu auf. Wurde der
#    web-Container zwischenzeitlich neu ERSTELLT (neue IP, z.B. durch ein
#    'docker compose up -d'), zeigt nginx sonst auf die alte IP -> 502.
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[4/6]${NC} Starte Container neu (lädt neuen Code)..."
docker compose restart web celery-worker celery-beat nginx
echo -e "${GREEN}  ✓ Neustart ausgelöst${NC}"

# ---------------------------------------------------------------------------
# 4) Migrationen explizit anwenden (sichtbar; idempotent, falls Entrypoint
#    sie schon ausgeführt hat). Kurz warten, bis web wieder erreichbar ist.
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[5/6]${NC} Wende Datenbank-Migrationen an..."
sleep 8
docker compose exec -T web python manage.py migrate --noinput
echo -e "${GREEN}  ✓ Migrationen aktuell${NC}"

# ---------------------------------------------------------------------------
# 5) Status prüfen
# ---------------------------------------------------------------------------
echo -e "\n${BLUE}[6/6]${NC} Prüfe Container-Status..."
sleep 5
if docker compose ps | grep -qE "unhealthy|Exit"; then
    echo -e "${RED}  ✗ Mindestens ein Container ist nicht gesund:${NC}"
    docker compose ps
    echo ""
    echo "Logs: docker compose logs -f"
    exit 1
fi
echo -e "${GREEN}  ✓ Alle Container laufen${NC}"

echo -e "\n${GREEN}=========================================="
echo "  Offline-Update abgeschlossen: $CURRENT → $NEW"
echo -e "==========================================${NC}"
echo ""
echo "  Backup:  $BACKUP_FILE"
echo "  Logs:    docker compose logs -f"
