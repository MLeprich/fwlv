#!/bin/bash
# =============================================================================
# FLVS - Internes HTTPS (Port 443) mit selbstsigniertem Zertifikat aktivieren
# =============================================================================
# Für den Betrieb hinter einem Reverse-Proxy, der das Backend über HTTPS/443
# anspricht (statt HTTP/80). Der interne nginx lauscht standardmäßig nur auf 80 –
# der Proxy bekommt dann "connection refused" auf 443.
#
# Das echte, vom Browser vertraute Zertifikat liegt beim vorgelagerten Proxy. Der
# interne Hop (Proxy -> VM) braucht auf einer abgeschotteten, internen VM kein
# öffentlich vertrautes Zertifikat – ein selbstsigniertes genügt. Der Proxy muss
# die Zertifikatsprüfung für dieses Backend ggf. deaktivieren (SSL verify off).
#
#   cd /opt/flvs && ./docker/scripts/enable-internal-https.sh
#
# Danach lauscht nginx zusätzlich auf 443. Port 80 bleibt bestehen.
# =============================================================================

set -e
cd "$(dirname "$0")/../.."

CERT_DIR="docker/certbot/conf/internal"
CONF_FILE="docker/nginx/conf.d/https-internal.conf"

# Domain aus der .env lesen (nur fürs Zertifikat-CN, funktional unerheblich)
DOMAIN="localhost"
if [[ -f .env ]]; then
    d=$(grep -E '^DOMAIN=' .env | cut -d= -f2- | tr -d '"' | tr -d "'")
    [[ -n "$d" ]] && DOMAIN="$d"
fi

echo "[1/4] Prüfe Voraussetzungen..."
if ! command -v openssl >/dev/null 2>&1; then
    echo "  FEHLER: openssl nicht gefunden. Bitte installieren (z.B. apt-get install openssl)."
    exit 1
fi

echo "[2/4] Erzeuge selbstsigniertes Zertifikat für '$DOMAIN' (10 Jahre gültig)..."
mkdir -p "$CERT_DIR"
if [[ -f "$CERT_DIR/privkey.pem" && -f "$CERT_DIR/fullchain.pem" ]]; then
    echo "  Vorhandenes Zertifikat gefunden – wird beibehalten. (Zum Neuerzeugen: $CERT_DIR löschen)"
else
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout "$CERT_DIR/privkey.pem" \
        -out "$CERT_DIR/fullchain.pem" \
        -subj "/CN=$DOMAIN" \
        -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1" 2>/dev/null
    chmod 600 "$CERT_DIR/privkey.pem"
    echo "  Zertifikat erstellt: $CERT_DIR/"
fi

echo "[3/4] Schreibe nginx-HTTPS-Konfiguration ($CONF_FILE)..."
# Pfade sind aus Sicht des nginx-CONTAINERS (Mount: docker/certbot/conf -> /etc/letsencrypt)
cat > "$CONF_FILE" <<'NGINX'
# =============================================================================
# FLVS - Internes HTTPS (Port 443), selbstsigniert
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
echo "  geschrieben."

echo "[4/4] nginx-Konfiguration prüfen und neu laden..."
if docker compose exec -T nginx nginx -t 2>/dev/null; then
    docker compose exec -T nginx nginx -s reload 2>/dev/null || docker compose restart nginx
    echo "  nginx neu geladen."
else
    # nginx läuft evtl. noch nicht (Erstinstallation) – dann reicht das Vorhandensein der Dateien
    echo "  nginx-Container nicht erreichbar – Konfiguration liegt bereit und wird beim Start aktiv."
fi

echo ""
echo "Fertig. nginx lauscht jetzt zusätzlich auf Port 443 (selbstsigniert)."
echo ""
echo "WICHTIG für den vorgelagerten Reverse-Proxy:"
echo "  - Backend auf https://<vm>:443 zeigen lassen UND"
echo "  - die Zertifikatsprüfung für dieses Backend deaktivieren"
echo "    (das interne Zertifikat ist selbstsigniert)."
echo ""
echo "Prüfen von der VM aus:"
echo "  curl -k -o /dev/null -w '%{http_code}\\n' https://localhost:443/"
