#!/bin/bash
# =============================================================================
# FLVS - Feuerwehr Lagerverwaltungssystem
# One-Click Installation Script
# =============================================================================
# Verwendung:
#   curl -fsSL https://raw.githubusercontent.com/MLeprich/fwlv/main/install.sh | bash
# oder:
#   ./install.sh [--domain example.com] [--email admin@example.com]
# =============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Standard-Werte
INSTALL_DIR="${INSTALL_DIR:-/opt/flvs}"
DOMAIN=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""
SKIP_DOCKER_INSTALL=false

# =============================================================================
# Funktionen
# =============================================================================

print_banner() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "  FLVS - Feuerwehr Lagerverwaltungssystem"
    echo "  Installation Script v1.0"
    echo "=============================================="
    echo -e "${NC}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warn "Dieses Skript sollte nicht als root ausgeführt werden."
        log_warn "Es wird sudo verwenden, wenn nötig."
    fi
}

check_system() {
    log_info "Prüfe Systemvoraussetzungen..."

    # OS prüfen
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        log_info "Betriebssystem: $NAME $VERSION_ID"
    fi

    # RAM prüfen
    total_ram=$(free -m | awk '/^Mem:/{print $2}')
    if [[ $total_ram -lt 3500 ]]; then
        log_warn "Weniger als 4GB RAM erkannt ($total_ram MB). Mindestens 4GB empfohlen."
    else
        log_info "RAM: ${total_ram}MB - OK"
    fi

    # Speicherplatz prüfen
    free_space=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
    if [[ $free_space -lt 15 ]]; then
        log_warn "Weniger als 15GB freier Speicher ($free_space GB). Mindestens 20GB empfohlen."
    else
        log_info "Freier Speicher: ${free_space}GB - OK"
    fi
}

install_docker() {
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log_info "Docker bereits installiert: $docker_version"
        return 0
    fi

    if [[ "$SKIP_DOCKER_INSTALL" == "true" ]]; then
        log_error "Docker nicht gefunden und --skip-docker-install gesetzt."
        exit 1
    fi

    log_info "Installiere Docker..."
    curl -fsSL https://get.docker.com | sh

    # Aktuellen Benutzer zur docker-Gruppe hinzufügen
    if [[ $EUID -ne 0 ]]; then
        sudo usermod -aG docker $USER
        log_warn "Benutzer zur docker-Gruppe hinzugefügt. Bitte neu einloggen oder 'newgrp docker' ausführen."
    fi

    log_info "Docker erfolgreich installiert."
}

install_dependencies() {
    log_info "Installiere Abhängigkeiten..."

    if command -v apt-get &> /dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq git curl openssl
    elif command -v yum &> /dev/null; then
        sudo yum install -y git curl openssl
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y git curl openssl
    else
        log_warn "Paketmanager nicht erkannt. Bitte git, curl und openssl manuell installieren."
    fi
}

clone_repository() {
    if [[ -d "$INSTALL_DIR" ]]; then
        log_info "Verzeichnis $INSTALL_DIR existiert bereits."
        read -p "Überschreiben? (j/N): " confirm
        if [[ "$confirm" =~ ^[jJyY]$ ]]; then
            sudo rm -rf "$INSTALL_DIR"
        else
            log_info "Installation abgebrochen."
            exit 0
        fi
    fi

    log_info "Klone Repository nach $INSTALL_DIR..."
    sudo git clone https://github.com/MLeprich/fwlv.git "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    cd "$INSTALL_DIR"
}

generate_secrets() {
    log_info "Generiere sichere Passwörter..."

    # Secret Key generieren
    SECRET_KEY=$(openssl rand -base64 50 | tr -dc 'a-zA-Z0-9' | head -c 50)

    # Datenbank-Passwort generieren
    DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 24)

    # Admin-Passwort generieren (falls nicht angegeben)
    if [[ -z "$ADMIN_PASSWORD" ]]; then
        ADMIN_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)
    fi
}

create_env_file() {
    log_info "Erstelle .env Konfiguration..."

    # Domain abfragen falls nicht angegeben
    if [[ -z "$DOMAIN" ]]; then
        read -p "Domain (z.B. flvs.meine-feuerwehr.de) [localhost]: " DOMAIN
        DOMAIN=${DOMAIN:-localhost}
    fi

    # Email abfragen falls nicht angegeben
    if [[ -z "$ADMIN_EMAIL" ]]; then
        read -p "Admin E-Mail [admin@$DOMAIN]: " ADMIN_EMAIL
        ADMIN_EMAIL=${ADMIN_EMAIL:-admin@$DOMAIN}
    fi

    cat > "$INSTALL_DIR/.env" << EOF
# =============================================================================
# FLVS - Automatisch generierte Konfiguration
# Erstellt am: $(date '+%Y-%m-%d %H:%M:%S')
# =============================================================================

# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1
DOMAIN=$DOMAIN

# Database
POSTGRES_DB=flvs
POSTGRES_USER=flvs
POSTGRES_PASSWORD=$DB_PASSWORD

# Redis
REDIS_URL=redis://redis:6379/1
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Ports
HTTP_PORT=80
HTTPS_PORT=443

# Superuser (wird beim ersten Start erstellt)
CREATE_SUPERUSER=true
SUPERUSER_USERNAME=admin
SUPERUSER_PASSWORD=$ADMIN_PASSWORD
SUPERUSER_EMAIL=$ADMIN_EMAIL

# Backup
BACKUP_RETENTION_DAYS=30
EOF

    chmod 600 "$INSTALL_DIR/.env"
    log_info ".env Datei erstellt."
}

create_directories() {
    log_info "Erstelle Verzeichnisse..."
    mkdir -p "$INSTALL_DIR/docker/backup"
    mkdir -p "$INSTALL_DIR/docker/certbot/conf"
    mkdir -p "$INSTALL_DIR/docker/certbot/www"
}

start_containers() {
    log_info "Starte Docker Container..."
    cd "$INSTALL_DIR"

    # Images bauen
    docker compose build --quiet

    # Container starten
    docker compose up -d

    log_info "Warte auf Container-Start..."
    sleep 10

    # Status prüfen
    if docker compose ps | grep -q "unhealthy\|Exit"; then
        log_error "Einige Container sind nicht gesund. Prüfe mit: docker compose logs"
        docker compose ps
        exit 1
    fi

    log_info "Alle Container gestartet."
}

init_database() {
    log_info "Initialisiere Datenbank..."

    # Warte bis Web-Container bereit ist
    max_attempts=30
    attempt=1
    while ! docker compose exec -T web python manage.py check &>/dev/null; do
        if [[ $attempt -ge $max_attempts ]]; then
            log_error "Web-Container nicht bereit nach $max_attempts Versuchen."
            exit 1
        fi
        log_info "Warte auf Web-Container... ($attempt/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done

    # Berechtigungen einrichten
    log_info "Richte Berechtigungen ein..."
    docker compose exec -T web python manage.py setup_permissions || true

    # Weitere Setup-Commands (falls vorhanden)
    for cmd in setup_medical_permissions setup_clothing_permissions setup_equipment_permissions; do
        docker compose exec -T web python manage.py $cmd 2>/dev/null || true
    done

    log_info "Datenbank initialisiert."
}

print_success() {
    echo ""
    echo -e "${GREEN}=============================================="
    echo "  Installation erfolgreich abgeschlossen!"
    echo "==============================================${NC}"
    echo ""
    echo -e "  ${BLUE}URL:${NC}      http://$DOMAIN/"
    echo -e "  ${BLUE}Admin:${NC}    http://$DOMAIN/admin/"
    echo ""
    echo -e "  ${YELLOW}Login-Daten:${NC}"
    echo -e "  Benutzer: admin"
    echo -e "  Passwort: $ADMIN_PASSWORD"
    echo ""
    echo -e "  ${RED}WICHTIG: Passwort nach erstem Login ändern!${NC}"
    echo ""
    echo -e "  ${BLUE}Nächste Schritte:${NC}"
    echo "  1. SSL aktivieren: ./docker/scripts/init-ssl.sh $DOMAIN $ADMIN_EMAIL"
    echo "  2. Backup aktivieren: docker compose --profile backup up -d"
    echo "  3. Dokumentation: $INSTALL_DIR/docs/DOCKER_INSTALLATION.md"
    echo ""
    echo "  Logs anzeigen: cd $INSTALL_DIR && docker compose logs -f"
    echo ""
}

save_credentials() {
    # Credentials in Datei speichern (nur für Admin lesbar)
    cat > "$INSTALL_DIR/.credentials" << EOF
# FLVS Zugangsdaten - $(date '+%Y-%m-%d %H:%M:%S')
# DIESE DATEI SICHER AUFBEWAHREN UND DANN LÖSCHEN!

URL: http://$DOMAIN/
Admin-URL: http://$DOMAIN/admin/

Benutzer: admin
Passwort: $ADMIN_PASSWORD
E-Mail: $ADMIN_EMAIL

Datenbank-Passwort: $DB_PASSWORD
EOF
    chmod 600 "$INSTALL_DIR/.credentials"
    log_info "Zugangsdaten gespeichert in: $INSTALL_DIR/.credentials"
}

# =============================================================================
# Argument-Parsing
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain)
            DOMAIN="$2"
            shift 2
            ;;
        --email)
            ADMIN_EMAIL="$2"
            shift 2
            ;;
        --password)
            ADMIN_PASSWORD="$2"
            shift 2
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --skip-docker-install)
            SKIP_DOCKER_INSTALL=true
            shift
            ;;
        --help|-h)
            echo "Verwendung: $0 [OPTIONEN]"
            echo ""
            echo "Optionen:"
            echo "  --domain DOMAIN       Domain für die Installation"
            echo "  --email EMAIL         Admin E-Mail-Adresse"
            echo "  --password PASSWORD   Admin Passwort (sonst generiert)"
            echo "  --install-dir DIR     Installationsverzeichnis (Standard: /opt/flvs)"
            echo "  --skip-docker-install Docker-Installation überspringen"
            echo "  --help, -h            Diese Hilfe anzeigen"
            exit 0
            ;;
        *)
            log_error "Unbekannte Option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Hauptprogramm
# =============================================================================

print_banner
check_root
check_system
install_dependencies
install_docker
clone_repository
generate_secrets
create_env_file
create_directories
start_containers
init_database
save_credentials
print_success
