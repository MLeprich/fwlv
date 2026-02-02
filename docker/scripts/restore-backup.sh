#!/bin/bash
# =============================================================================
# FLVS - Database Restore Script
# =============================================================================
# Stellt eine Datenbank-Backup-Datei wieder her.
#
# Verwendung:
#   ./docker/scripts/restore-backup.sh backup_file.sql.gz
#
# Vom Host aus:
#   docker compose exec db sh -c 'gunzip -c /backup/flvs_backup_20240101.sql.gz | psql -U $POSTGRES_USER -d $POSTGRES_DB'
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Fehler: Backup-Datei nicht angegeben${NC}"
    echo ""
    echo "Verwendung: $0 <backup_file.sql.gz>"
    echo ""
    echo "Verfügbare Backups:"
    ls -la /backup/*.sql.gz 2>/dev/null || echo "  Keine Backups gefunden in /backup/"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    # Prüfe ob die Datei im Backup-Verzeichnis liegt
    if [ -f "/backup/$BACKUP_FILE" ]; then
        BACKUP_FILE="/backup/$BACKUP_FILE"
    else
        echo -e "${RED}Fehler: Backup-Datei nicht gefunden: $BACKUP_FILE${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}=========================================="
echo "FLVS - Datenbank-Wiederherstellung"
echo -e "==========================================${NC}"
echo ""
echo -e "${YELLOW}WARNUNG: Dies löscht die aktuelle Datenbank!${NC}"
echo "Backup-Datei: $BACKUP_FILE"
echo ""
read -p "Fortfahren? (ja/nein): " confirm

if [[ "$confirm" != "ja" && "$confirm" != "yes" ]]; then
    echo "Abgebrochen."
    exit 0
fi

echo -e "\n${BLUE}[1/3]${NC} Lösche aktuelle Datenbank..."
dropdb -h "$PGHOST" -U "$PGUSER" "$PGDATABASE" --if-exists
createdb -h "$PGHOST" -U "$PGUSER" "$PGDATABASE"
echo -e "${GREEN}  ✓ Datenbank neu erstellt${NC}"

echo -e "\n${BLUE}[2/3]${NC} Stelle Backup wieder her..."
gunzip -c "$BACKUP_FILE" | psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -q
echo -e "${GREEN}  ✓ Backup wiederhergestellt${NC}"

echo -e "\n${BLUE}[3/3]${NC} Führe Migrationen aus..."
python manage.py migrate --noinput
echo -e "${GREEN}  ✓ Migrationen abgeschlossen${NC}"

echo -e "\n${GREEN}=========================================="
echo "  Wiederherstellung abgeschlossen!"
echo -e "==========================================${NC}"
echo ""
echo "Die Datenbank wurde aus dem Backup wiederhergestellt."
echo "Bitte starten Sie die Anwendung neu: docker compose restart web"
echo ""
