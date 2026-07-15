#!/bin/bash
# =============================================================================
# FLVS - Internes HTTPS (Port 443) für den Betrieb hinter einem Reverse-Proxy
# =============================================================================
# Der interne nginx lauscht standardmäßig nur auf Port 80. Spricht der vorgelagerte
# Reverse-Proxy das Backend über HTTPS/443 an, bekommt er "connection refused".
# Dieses Skript aktiviert einen 443-Server-Block. Port 80 bleibt erhalten.
#
# DREI Wege, an das interne Zertifikat zu kommen:
#
#   1) Zertifikat von der internen Stadt-CA (EMPFOHLEN, wenn vorhanden):
#        ./enable-internal-https.sh --csr        # erzeugt Schlüssel + Antrag (CSR)
#        # CSR beim Zertifikatsserver einreichen, signiertes Zertifikat als
#        # docker/certbot/conf/internal/fullchain.pem ablegen, dann:
#        ./enable-internal-https.sh              # aktiviert 443 mit diesem Zertifikat
#      Vorteil: Der Proxy vertraut der Stadt-CA -> KEIN "SSL verify off" nötig.
#
#   2) Fertiges Zertifikat einspielen (z.B. schon zugewiesen bekommen):
#        ./enable-internal-https.sh --cert /pfad/cert.pem --key /pfad/key.pem
#
#   3) Selbstsigniert (Fallback, ohne CA):
#        ./enable-internal-https.sh --self-signed
#      Der Proxy muss dann die Zertifikatsprüfung fürs Backend deaktivieren.
#
# Der private Schlüssel verlässt die VM NIE – nur der CSR geht zum Zertifikatsserver.
# =============================================================================

set -e
cd "$(dirname "$0")/../.."

CERT_DIR="docker/certbot/conf/internal"
CONF_FILE="docker/nginx/conf.d/https-internal.conf"
MODE=""           # csr | self-signed | (leer = aktivieren mit vorhandenem Zertifikat)
CERT_IN=""
KEY_IN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --csr)         MODE="csr"; shift ;;
        --self-signed) MODE="self-signed"; shift ;;
        --cert)        CERT_IN="$2"; shift 2 ;;
        --key)         KEY_IN="$2"; shift 2 ;;
        --help|-h)
            grep '^#' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "Unbekannte Option: $1"; exit 1 ;;
    esac
done

# Domain aus der .env (fürs Zertifikat-CN)
DOMAIN="localhost"
if [[ -f .env ]]; then
    d=$(grep -E '^DOMAIN=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
    [[ -n "$d" ]] && DOMAIN="$d"
fi

command -v openssl >/dev/null 2>&1 || { echo "FEHLER: openssl fehlt."; exit 1; }
mkdir -p "$CERT_DIR"

# ---------------------------------------------------------------------------
# Modus 1a: CSR erzeugen und aufhören (Zertifikat kommt von der CA)
# ---------------------------------------------------------------------------
if [[ "$MODE" == "csr" ]]; then
    echo "[CSR] Erzeuge privaten Schlüssel und Zertifikatsantrag für '$DOMAIN'..."
    openssl req -new -nodes -newkey rsa:2048 \
        -keyout "$CERT_DIR/privkey.pem" \
        -out "$CERT_DIR/request.csr" \
        -subj "/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1" 2>/dev/null
    chmod 600 "$CERT_DIR/privkey.pem"
    echo ""
    echo "Fertig. Nächste Schritte:"
    echo "  1. Diesen Antrag beim Zertifikatsserver der Stadt einreichen:"
    echo "       $CERT_DIR/request.csr"
    echo "  2. Das signierte Zertifikat (inkl. Zwischenzertifikate, PEM) ablegen als:"
    echo "       $CERT_DIR/fullchain.pem"
    echo "     (Der private Schlüssel $CERT_DIR/privkey.pem bleibt hier – NICHT weitergeben.)"
    echo "  3. Danach 443 aktivieren:"
    echo "       ./docker/scripts/enable-internal-https.sh"
    exit 0
fi

# ---------------------------------------------------------------------------
# Modus 2: bereitgestelltes Zertifikat einspielen
# ---------------------------------------------------------------------------
if [[ -n "$CERT_IN" || -n "$KEY_IN" ]]; then
    [[ -f "$CERT_IN" ]] || { echo "FEHLER: --cert Datei nicht gefunden: $CERT_IN"; exit 1; }
    [[ -f "$KEY_IN"  ]] || { echo "FEHLER: --key Datei nicht gefunden: $KEY_IN"; exit 1; }
    cp "$CERT_IN" "$CERT_DIR/fullchain.pem"
    cp "$KEY_IN"  "$CERT_DIR/privkey.pem"
    chmod 600 "$CERT_DIR/privkey.pem"
    echo "[Zertifikat] Eingespielt aus $CERT_IN / $KEY_IN."
fi

# ---------------------------------------------------------------------------
# Modus 3: selbstsigniert (nur wenn ausdrücklich gewünscht oder nichts da)
# ---------------------------------------------------------------------------
if [[ "$MODE" == "self-signed" ]]; then
    echo "[Selbstsigniert] Erzeuge Zertifikat für '$DOMAIN' (10 Jahre)..."
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout "$CERT_DIR/privkey.pem" -out "$CERT_DIR/fullchain.pem" \
        -subj "/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1" 2>/dev/null
    chmod 600 "$CERT_DIR/privkey.pem"
fi

# ---------------------------------------------------------------------------
# Ab hier: Zertifikat muss vorliegen, sonst Hinweis geben
# ---------------------------------------------------------------------------
if [[ ! -f "$CERT_DIR/fullchain.pem" || ! -f "$CERT_DIR/privkey.pem" ]]; then
    echo ""
    echo "Es liegt noch kein Zertifikat unter $CERT_DIR/ vor. Wähle einen Weg:"
    echo "  - Von der Stadt-CA:   ./docker/scripts/enable-internal-https.sh --csr"
    echo "  - Fertiges Zertifikat: ./docker/scripts/enable-internal-https.sh --cert cert.pem --key key.pem"
    echo "  - Selbstsigniert:      ./docker/scripts/enable-internal-https.sh --self-signed"
    exit 1
fi

# Schlüssel und Zertifikat müssen zusammenpassen (häufiger Kopierfehler)
c_mod=$(openssl x509 -noout -modulus -in "$CERT_DIR/fullchain.pem" 2>/dev/null | openssl md5)
k_mod=$(openssl rsa  -noout -modulus -in "$CERT_DIR/privkey.pem"   2>/dev/null | openssl md5)
if [[ "$c_mod" != "$k_mod" ]]; then
    echo "FEHLER: Zertifikat und privater Schlüssel passen nicht zusammen."
    echo "  Prüfe $CERT_DIR/fullchain.pem und $CERT_DIR/privkey.pem."
    exit 1
fi

echo "[nginx] Schreibe HTTPS-Konfiguration ($CONF_FILE)..."
cat > "$CONF_FILE" <<'NGINX'
# =============================================================================
# FLVS - Internes HTTPS (Port 443)
# Automatisch erzeugt von docker/scripts/enable-internal-https.sh – nicht manuell
# bearbeiten. Für den Betrieb hinter einem Reverse-Proxy, der das Backend per 443
# anspricht. Das öffentlich vertraute Zertifikat liegt beim vorgelagerten Proxy.
# =============================================================================
server {
    listen 443 ssl;
    http2 on;
    server_name _;

    ssl_certificate     /etc/letsencrypt/internal/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/internal/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    include /etc/nginx/conf.d/app.include;
}
NGINX

echo "[nginx] Konfiguration prüfen und neu laden..."
if docker compose exec -T nginx nginx -t 2>/dev/null; then
    docker compose exec -T nginx nginx -s reload 2>/dev/null || docker compose restart nginx
    echo "  nginx neu geladen."
else
    echo "  nginx-Container nicht erreichbar – Konfiguration liegt bereit und wird beim Start aktiv."
fi

# Selbstsigniert erkennt man am identischen Aussteller/Inhaber -> Hinweis für den Proxy
issuer=$(openssl x509 -noout -issuer -in "$CERT_DIR/fullchain.pem" 2>/dev/null)
subject=$(openssl x509 -noout -subject -in "$CERT_DIR/fullchain.pem" 2>/dev/null)
echo ""
echo "Fertig. nginx lauscht jetzt zusätzlich auf Port 443."
echo "  Aussteller: ${issuer#issuer=}"
if [[ "${issuer#issuer=}" == "${subject#subject=}" ]]; then
    echo ""
    echo "  Hinweis: Das Zertifikat ist SELBSTSIGNIERT. Der vorgelagerte Proxy muss die"
    echo "  Zertifikatsprüfung für dieses Backend deaktivieren (SSL verify off)."
    echo "  Sauberer wäre ein Zertifikat der Stadt-CA (--csr)."
fi
echo ""
echo "Prüfen von der VM aus:"
echo "  curl -k -o /dev/null -w '%{http_code}\\n' https://localhost:443/"
