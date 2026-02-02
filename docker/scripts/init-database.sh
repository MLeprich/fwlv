#!/bin/bash
# =============================================================================
# FLVS - Database Initialization Script
# =============================================================================
# Initialisiert die Datenbank mit allen benötigten Tabellen, Permissions und
# optional mit einem Superuser.
#
# Verwendung (innerhalb des Docker-Containers):
#   ./docker/scripts/init-database.sh
#
# Oder vom Host aus:
#   docker compose exec web ./docker/scripts/init-database.sh
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "FLVS - Datenbank-Initialisierung"
echo -e "==========================================${NC}"

# 1. Migrationen ausführen
echo -e "\n${BLUE}[1/5]${NC} Führe Migrationen aus..."
python manage.py migrate --noinput
echo -e "${GREEN}  ✓ Migrationen abgeschlossen${NC}"

# 2. Static Files sammeln
echo -e "\n${BLUE}[2/5]${NC} Sammle Static Files..."
python manage.py collectstatic --noinput
echo -e "${GREEN}  ✓ Static Files gesammelt${NC}"

# 3. Permissions und Rollen einrichten
echo -e "\n${BLUE}[3/5]${NC} Richte Permissions und Rollen ein..."
python manage.py setup_permissions || echo -e "${YELLOW}  ! Warnung: setup_permissions fehlgeschlagen${NC}"
echo -e "${GREEN}  ✓ Basis-Permissions eingerichtet${NC}"

# 4. Modul-spezifische Permissions
echo -e "\n${BLUE}[4/5]${NC} Richte Modul-Permissions ein..."
declare -a modules=(
    "setup_medical_permissions"
    "setup_clothing_permissions"
    "setup_equipment_permissions"
    "setup_magazine_permissions"
    "setup_height_rescue_permissions"
    "setup_diving_permissions"
    "setup_workshop_permissions"
    "setup_it_hardware_permissions"
)

for cmd in "${modules[@]}"; do
    if python manage.py $cmd 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $cmd"
    else
        echo -e "  ${YELLOW}-${NC} $cmd (nicht verfügbar oder bereits eingerichtet)"
    fi
done

# 5. Superuser erstellen (falls angefordert)
echo -e "\n${BLUE}[5/5]${NC} Superuser-Prüfung..."

if [ "$CREATE_SUPERUSER" = "true" ] || [ "$1" = "--create-superuser" ]; then
    SUPERUSER_USERNAME=${SUPERUSER_USERNAME:-admin}
    SUPERUSER_EMAIL=${SUPERUSER_EMAIL:-admin@flvs.local}
    SUPERUSER_PASSWORD=${SUPERUSER_PASSWORD:-changeme123}

    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = '$SUPERUSER_USERNAME'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(
        username=username,
        email='$SUPERUSER_EMAIL',
        password='$SUPERUSER_PASSWORD'
    )
    print(f"  ✓ Superuser '{username}' erstellt!")
else:
    print(f"  - User '{username}' existiert bereits.")
EOF
else
    echo -e "  ${YELLOW}-${NC} Superuser-Erstellung übersprungen (--create-superuser oder CREATE_SUPERUSER=true setzen)"
fi

# Zusammenfassung
echo -e "\n${GREEN}=========================================="
echo "  Initialisierung abgeschlossen!"
echo -e "==========================================${NC}"

# Zeige Gruppen-Übersicht
echo -e "\n${BLUE}Eingerichtete Rollen:${NC}"
python manage.py shell << EOF
from django.contrib.auth.models import Group
groups = Group.objects.all().order_by('name')
for g in groups:
    print(f"  - {g.name} ({g.permissions.count()} Permissions)")
print(f"\nGesamt: {groups.count()} Rollen")
EOF

echo -e "\n${BLUE}Nächste Schritte:${NC}"
echo "  1. Admin-Login unter: http://localhost/admin/"
echo "  2. Benutzer anlegen und Rollen zuweisen"
echo "  3. Module über Einstellungen aktivieren/deaktivieren"
echo ""
