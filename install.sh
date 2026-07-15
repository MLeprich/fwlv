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
OFFLINE=false
IMAGE_BUNDLE=""
# Betrieb hinter einem vorgelagerten Reverse-Proxy, der SSL terminiert (z.B. Stadt-RZ).
REVERSE_PROXY=false

# Pfad des laufenden Skripts (für die Selbstlösch-Prüfung und die Versionsanzeige)
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# =============================================================================
# Funktionen
# =============================================================================

print_banner() {
    # Commit des laufenden Skripts anzeigen. Sonst lässt sich hinterher aus dem
    # Protokoll nicht erkennen, ob eine veraltete Fassung ausgeführt wurde.
    local version="unbekannt"
    if command -v git &>/dev/null && git -C "$SCRIPT_DIR" rev-parse --short HEAD &>/dev/null; then
        version="$(git -C "$SCRIPT_DIR" rev-parse --short HEAD)"
    fi

    echo -e "${BLUE}"
    echo "=============================================="
    echo "  FLVS - Feuerwehr Lagerverwaltungssystem"
    echo "  Installation Script"
    echo "  Skript: $SCRIPT_PATH"
    echo "  Stand:  $version"
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

    # RAM prüfen (locale-unabhängig über /proc/meminfo statt `free`,
    # dessen Spaltenlabel bei z.B. deutscher Locale "Speicher:" statt "Mem:" heißt)
    total_ram=$(awk '/^MemTotal:/ {print int($2/1024)}' /proc/meminfo 2>/dev/null)
    if [[ -z "$total_ram" ]]; then
        log_warn "RAM konnte nicht ermittelt werden."
    elif [[ $total_ram -lt 3500 ]]; then
        log_warn "Weniger als 4GB RAM erkannt (${total_ram} MB). Mindestens 4GB empfohlen."
    else
        log_info "RAM: ${total_ram}MB - OK"
    fi

    # Speicherplatz prüfen – und zwar dort, wo er wirklich gebraucht wird.
    #
    # Ein Blick auf "/" sagt nichts aus, wenn /var oder /opt eigene Partitionen sind.
    # Zwei Orte zählen:
    #   1. Docker-Datenverzeichnis (meist /var/lib/docker): hier landen die Images
    #      (~1,8 GB), die Container und die Volumes (Datenbank, Medien, Logs) – sie
    #      wachsen mit der Nutzung. Bei einem Update liegen kurzzeitig ALTE und NEUE
    #      Images nebeneinander.
    #   2. Installationsverzeichnis: Repository (~50 MB) und, im Offline-Modus, das
    #      Image-Bundle (~420 MB). Das Bundle kann nach dem Laden gelöscht werden.
    check_free_space() {
        local pfad="$1" label="$2" minimum="$3"

        local frei
        frei=$(LC_ALL=C df -P -BG "$pfad" 2>/dev/null | awk 'NR==2 {gsub(/G/,"",$4); print $4}')
        if [[ -z "$frei" ]]; then
            log_warn "Freier Speicher für $label konnte nicht ermittelt werden."
            return 0
        fi

        local geraet
        geraet=$(LC_ALL=C df -P "$pfad" 2>/dev/null | awk 'NR==2 {print $1}')

        if [[ $frei -lt $minimum ]]; then
            log_error "$label ($pfad, $geraet): nur ${frei} GB frei – mindestens ${minimum} GB nötig."
            return 1
        fi
        log_info "$label ($pfad): ${frei} GB frei - OK"
        return 0
    }

    local docker_root="/var/lib/docker"
    if command -v docker &>/dev/null; then
        docker_root=$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo /var/lib/docker)
    fi
    # Existiert das Verzeichnis noch nicht, prüfen wir das darüberliegende.
    [[ -d "$docker_root" ]] || docker_root=$(dirname "$docker_root")

    local install_root="$INSTALL_DIR"
    [[ -d "$install_root" ]] || install_root=$(dirname "$install_root")

    local platz_ok=0
    # 8 GB: Images (~1,8) + Volumes + Container + Reserve für ein Update, bei dem
    # alte und neue Images kurzzeitig nebeneinander liegen.
    check_free_space "$docker_root" "Docker-Daten (Images, Datenbank, Medien)" 8 || platz_ok=1
    # 1 GB: Repository + Image-Bundle im Offline-Modus.
    check_free_space "$install_root" "Installationsverzeichnis" 1 || platz_ok=1

    if [[ $platz_ok -ne 0 ]]; then
        log_error ""
        log_error "Zu wenig Speicherplatz. Die Installation würde mitten im Laden der Images"
        log_error "abbrechen (typisch: 'unexpected EOF' bei docker load)."
        log_error ""
        log_error "Platzbedarf im Überblick:"
        log_error "  Docker-Daten ($docker_root):"
        log_error "    ~1,8 GB  Images"
        log_error "    + Volumes (Datenbank, Medien, Logs) – wachsen mit der Nutzung"
        log_error "    + Reserve für Updates (alte und neue Images liegen kurz nebeneinander)"
        log_error "  Installationsverzeichnis ($install_root):"
        log_error "    ~50 MB   Repository"
        log_error "    ~420 MB  Image-Bundle (kann nach dem Laden gelöscht werden)"
        log_error ""
        log_error "Empfehlung: 20 GB auf dem Dateisystem mit $docker_root."
        exit 1
    fi
}

check_script_location() {
    # Im Online-Modus wird $INSTALL_DIR vor dem Klonen gelöscht. Liegt das laufende
    # Skript darin, löscht es sich dabei selbst. Bash liest danach weiter aus dem
    # gelöschten Inode – also mit der ALTEN Logik –, während auf der Platte schon die
    # frisch geklonte Fassung liegt. Genau so laufen veraltete Skriptstände unbemerkt
    # weiter und ignorieren z.B. den erst später hinzugekommenen Offline-Modus.
    if [[ "$OFFLINE" == "true" ]]; then
        return 0
    fi
    if [[ ! -d "$INSTALL_DIR" ]]; then
        return 0
    fi
    if [[ "$SCRIPT_PATH" != "$INSTALL_DIR"/* ]]; then
        return 0
    fi

    log_error "Dieses Skript liegt in $INSTALL_DIR und würde sich beim Überschreiben selbst löschen."
    log_error "Die Installation liefe dann mit der alten Skript-Version weiter."
    log_error ""
    log_error "Abhilfe – eine der beiden Varianten:"
    log_error "  a) Offline installieren (kein Klon, kein Build, kein Netz):"
    log_error "       cd $INSTALL_DIR && ./install.sh --offline"
    log_error "  b) Skript herauskopieren und von außerhalb starten:"
    log_error "       cp $SCRIPT_PATH ~/install.sh && ~/install.sh"
    exit 1
}

check_connectivity() {
    # Nur relevant, wenn geklont und gebaut wird. Der Offline-Modus braucht kein Netz.
    if [[ "$OFFLINE" == "true" ]]; then
        return 0
    fi

    log_info "Prüfe Erreichbarkeit der benötigten Gegenstellen..."

    # Was die Online-Installation tatsächlich anfasst:
    #   github.com        -> git clone des Repositories
    #   auth.docker.io    -> Basis-Image python:3.12-slim beim Build
    #   pypi.org          -> pip install im Dockerfile
    #   deb.debian.org    -> apt-get im Dockerfile
    local ziele=(
        "https://github.com|GitHub (git clone)"
        "https://auth.docker.io|Docker Hub (Basis-Images)"
        "https://pypi.org|PyPI (pip install im Build)"
        "http://deb.debian.org|Debian-Repos (apt im Build)"
    )

    # KEIN -f: manche dieser Hosts antworten auf ein nacktes GET mit 4xx (z.B.
    # auth.docker.io -> 404). Das ist trotzdem eine Antwort und beweist Erreichbarkeit.
    # -f würde sie als Fehler werten und auf intakter Verbindung fälschlich abbrechen.
    # Ohne -f meldet curl nur echte Verbindungsprobleme (Timeout/DNS/refused).
    local nicht_erreichbar=()
    for eintrag in "${ziele[@]}"; do
        local url="${eintrag%%|*}"
        local name="${eintrag##*|}"
        if curl -sS --max-time 8 -o /dev/null "$url" 2>/dev/null; then
            log_info "  erreichbar: $name"
        else
            log_warn "  NICHT erreichbar: $name"
            nicht_erreichbar+=("$name")
        fi
    done

    if [[ ${#nicht_erreichbar[@]} -gt 0 ]]; then
        log_error ""
        log_error "Die Online-Installation braucht alle vier Gegenstellen, ${#nicht_erreichbar[@]} davon sind nicht erreichbar."
        log_error "Auf einer abgeschotteten VM ist das der Normalfall – dafür gibt es den Offline-Modus:"
        log_error ""
        log_error "  1. Auf einer Maschine MIT Internet:"
        log_error "       ./docker/scripts/build-offline-bundle.sh"
        log_error "  2. Repository und flvs-images.tar auf diese VM kopieren"
        log_error "  3. Hier:"
        log_error "       ./install.sh --offline"
        log_error ""
        log_error "Der Offline-Modus baut nichts und klont nichts – er braucht überhaupt kein Netz."
        exit 1
    fi

    # Ein Proxy, der `docker pull` bedient, deckt den Build nicht automatisch mit ab:
    # BuildKit läuft in einem eigenen Kontext und erbt die Proxy-Variablen nicht.
    if [[ -n "${HTTP_PROXY:-}${HTTPS_PROXY:-}${http_proxy:-}${https_proxy:-}" ]]; then
        log_warn "Proxy-Umgebung erkannt. Docker BuildKit übernimmt diese NICHT automatisch."
        log_warn "Falls der Build an apt/pip hängenbleibt: Proxy in ~/.docker/config.json unter"
        log_warn "\"proxies\" eintragen – oder einfacher: --offline verwenden."
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

    # Offline: kein Paket-Repository erreichbar. git/curl/openssl müssen vorhanden sein.
    if [[ "$OFFLINE" == "true" ]]; then
        local missing=""
        for tool in git curl openssl; do
            command -v "$tool" &>/dev/null || missing="$missing $tool"
        done
        if [[ -n "$missing" ]]; then
            log_error "Offline-Modus: folgende Programme fehlen und müssen vorab installiert werden:$missing"
            exit 1
        fi
        log_info "Offline-Modus: benötigte Programme vorhanden."
        return 0
    fi

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
    # Offline-Modus: Repository muss bereits lokal vorliegen (kein GitHub-Zugriff)
    if [[ "$OFFLINE" == "true" ]]; then
        if [[ -d "$INSTALL_DIR/.git" ]]; then
            log_info "Offline-Modus: Verwende vorhandenes Repository in $INSTALL_DIR."
            cd "$INSTALL_DIR"
            return 0
        fi
        log_error "Offline-Modus: Kein Repository unter $INSTALL_DIR gefunden."
        log_error "Bitte das Repository vorab dorthin kopieren."
        exit 1
    fi

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

    # Reverse-Proxy-Modus: der vorgelagerte Proxy terminiert SSL, unser Stack läuft intern
    # per HTTP und vertraut dessen X-Forwarded-Proto. Sonst: reines HTTP ohne Proxy.
    if [[ "$REVERSE_PROXY" == "true" ]]; then
        USE_SSL=false
        TRUST_PROXY_SSL_HEADER=true
        log_info "Reverse-Proxy-Modus: USE_SSL=false, TRUST_PROXY_SSL_HEADER=true"
        log_info "  -> Der vorgelagerte Proxy MUSS die Header X-Forwarded-Proto: https und Host setzen."
    else
        USE_SSL=false
        TRUST_PROXY_SSL_HEADER=false
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

# SSL: terminiert unser eigener nginx das HTTPS? Bei einem vorgelagerten Reverse-Proxy
# bleibt das false (der Proxy macht SSL), sonst false bis ein Zertifikat eingerichtet ist.
USE_SSL=$USE_SSL

# Betrieb hinter einem TLS-terminierenden Proxy (Proxy spricht außen HTTPS, intern HTTP):
# true, damit Django dem X-Forwarded-Proto-Header vertraut. Sonst scheitert die Anmeldung
# mit "403 CSRF verification failed". Der Proxy muss X-Forwarded-Proto: https setzen.
TRUST_PROXY_SSL_HEADER=$TRUST_PROXY_SSL_HEADER

# CSRF: wird automatisch aus DOMAIN abgeleitet (https und http). Nur setzen, wenn die
# Anwendung unter weiteren Namen erreichbar ist – kommagetrennt MIT Schema, z.B.:
# CSRF_TRUSTED_ORIGINS=https://fwlager.rz.oberhausen.de,https://kurzname

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

    if [[ "$OFFLINE" == "true" ]]; then
        # Offline: Images aus vorbereitetem Bundle laden statt bauen (kein Docker-Hub-Zugriff)
        local bundle="${IMAGE_BUNDLE:-$INSTALL_DIR/flvs-images.tar}"
        if [[ ! -f "$bundle" ]]; then
            log_error "Offline-Modus: Image-Bundle nicht gefunden: $bundle"
            log_error "Bundle auf einer Maschine MIT Internet erstellen:"
            log_error "  ./docker/scripts/build-offline-bundle.sh"
            log_error "und die Datei nach $bundle kopieren (oder --image-bundle PFAD angeben)."
            exit 1
        fi
        # Das Bundle prüfen, BEVOR docker load daran scheitert. Eine unterbrochene
        # Übertragung (abgebrochener Download, volle Platte) hinterlässt eine
        # abgeschnittene Datei – docker load meldet dann nur "unexpected EOF" und
        # verrät nicht, dass die Datei selbst das Problem ist.
        log_info "Offline-Modus: Prüfe Image-Bundle ..."
        local groesse
        groesse=$(stat -c %s "$bundle" 2>/dev/null || echo 0)
        if [[ $groesse -lt 100000000 ]]; then
            log_error "Das Image-Bundle ist nur $((groesse / 1024 / 1024)) MB groß – erwartet werden ~420 MB."
            log_error "Die Datei ist unvollständig übertragen worden: $bundle"
            log_error ""
            log_error "Häufigste Ursache: die Platte lief beim Herunterladen/Kopieren voll."
            log_error "Datei löschen, Platz schaffen und erneut übertragen."
            exit 1
        fi
        if ! tar -tf "$bundle" >/dev/null 2>&1; then
            log_error "Das Image-Bundle ist beschädigt oder unvollständig: $bundle"
            log_error "($(du -h "$bundle" | cut -f1) vorhanden, aber das Archiv lässt sich nicht lesen.)"
            log_error ""
            log_error "Häufigste Ursache: der Download wurde abgebrochen, oft weil die Platte voll lief."
            log_error "Datei löschen, Platz schaffen und erneut übertragen:"
            log_error "  rm -f $bundle"
            log_error "  curl -L -o $bundle \\"
            log_error "    https://github.com/MLeprich/fwlv/releases/latest/download/flvs-images.tar"
            exit 1
        fi
        log_info "Image-Bundle vollständig ($(du -h "$bundle" | cut -f1))."

        log_info "Offline-Modus: Lade Images aus $bundle ..."
        docker load -i "$bundle"

        # Container starten OHNE Build und OHNE Registry-Zugriff. --pull never sorgt
        # dafür, dass ein fehlendes Image hart fehlschlägt, statt still nachgeladen zu
        # werden – auf einer abgeschotteten VM gäbe es diese zweite Chance ohnehin nicht.
        docker compose up -d --no-build --pull never
    else
        # Images bauen
        docker compose build --quiet

        # Container starten
        docker compose up -d
    fi

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
    for cmd in setup_medical_permissions setup_clothing_permissions setup_equipment_permissions \
                setup_magazine_permissions setup_height_rescue_permissions setup_diving_permissions \
                setup_workshop_permissions setup_it_hardware_permissions; do
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
        --offline)
            OFFLINE=true
            shift
            ;;
        --image-bundle)
            IMAGE_BUNDLE="$2"
            shift 2
            ;;
        --reverse-proxy)
            REVERSE_PROXY=true
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
            echo "  --offline             Offline-Modus: Images aus Bundle laden statt bauen"
            echo "                        (Repo muss lokal vorliegen, kein GitHub/Docker-Hub-Zugriff)"
            echo "  --image-bundle PFAD   Pfad zum Image-Bundle (Standard: <install-dir>/flvs-images.tar)"
            echo "  --reverse-proxy       Betrieb hinter einem SSL-terminierenden Reverse-Proxy"
            echo "                        (setzt USE_SSL=false, TRUST_PROXY_SSL_HEADER=true)"
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
check_script_location
check_connectivity
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
