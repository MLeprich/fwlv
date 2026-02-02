#!/bin/bash
# =============================================================================
# FLVS - Update Script
# =============================================================================
# Aktualisiert die FLVS-Installation auf die neueste Version.
#
# Verwendung:
#   ./docker/scripts/update.sh
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}=========================================="
echo "FLVS - System-Update"
echo -e "==========================================${NC}"
echo ""
echo "Installations-Verzeichnis: $INSTALL_DIR"

cd "$INSTALL_DIR"

# Aktuellen Status anzeigen
echo -e "\n${BLUE}[1/6]${NC} Prüfe Git-Status..."
CURRENT_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
echo "  Aktuelle Version: $CURRENT_VERSION"

# Backup erstellen
echo -e "\n${BLUE}[2/6]${NC} Erstelle Backup der Datenbank..."
docker compose exec -T db pg_dump -U flvs flvs | gzip > "$INSTALL_DIR/docker/backup/pre-update_$(date +%Y%m%d_%H%M%S).sql.gz"
echo -e "${GREEN}  ✓ Backup erstellt${NC}"

# Pull neueste Änderungen
echo -e "\n${BLUE}[3/6]${NC} Lade neueste Version..."
git fetch --all
git pull origin main
NEW_VERSION=$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)
echo -e "${GREEN}  ✓ Aktualisiert auf: $NEW_VERSION${NC}"

# Container neu bauen
echo -e "\n${BLUE}[4/6]${NC} Baue Container neu..."
docker compose build --quiet
echo -e "${GREEN}  ✓ Container gebaut${NC}"

# Container neu starten
echo -e "\n${BLUE}[5/6]${NC} Starte Container neu..."
docker compose up -d
echo -e "${GREEN}  ✓ Container gestartet${NC}"

# Warte auf Gesundheitsprüfung
echo -e "\n${BLUE}[6/6]${NC} Warte auf Container-Start..."
sleep 10

# Status prüfen
if docker compose ps | grep -q "unhealthy\|Exit"; then
    echo -e "${RED}  ✗ Einige Container sind nicht gesund!${NC}"
    docker compose ps
    echo ""
    echo "Logs anzeigen mit: docker compose logs -f"
    exit 1
fi

echo -e "${GREEN}  ✓ Alle Container sind gesund${NC}"

echo -e "\n${GREEN}=========================================="
echo "  Update erfolgreich abgeschlossen!"
echo -e "==========================================${NC}"
echo ""
echo "  Von: $CURRENT_VERSION"
echo "  Auf: $NEW_VERSION"
echo ""
echo "  Logs anzeigen: docker compose logs -f"
echo ""
