#!/bin/bash
# =============================================================================
# FLVS - Offline Image Bundle Builder
# =============================================================================
# Baut alle benötigten Docker-Images und exportiert sie in eine einzelne
# Datei (flvs-images.tar), damit FLVS auf einer VM OHNE Internetzugang
# installiert werden kann.
#
# AUSFÜHREN AUF EINER MASCHINE MIT INTERNET + Docker:
#   ./docker/scripts/build-offline-bundle.sh [ausgabedatei.tar]
#
# Anschließend die .tar-Datei zusammen mit dem Repository auf die Ziel-VM
# kopieren (nach <install-dir>/flvs-images.tar) und dort installieren mit:
#   ./install.sh --offline
# =============================================================================

set -e

# Ins Repo-Root wechseln (Skript liegt in docker/scripts/)
cd "$(dirname "$0")/../.."

OUT="${1:-flvs-images.tar}"

# Basis-Images: müssen exakt zu docker-compose.yml passen
BASE_IMAGES="postgres:16-alpine redis:7-alpine nginx:alpine"

# Anwendungs-Images: entsprechen den image:-Tags in docker-compose.yml
APP_IMAGES="flvs-web:local flvs-celery-worker:local flvs-celery-beat:local"

# -----------------------------------------------------------------------------
# Dieses Skript gehört NICHT auf die abgeschottete Ziel-VM.
#
# Es BAUT die Images (apt + pip im Container) und ZIEHT die Basis-Images vom Docker
# Hub – ohne Internet kann das gar nicht funktionieren. Auf der Ziel-VM wird
# stattdessen nur das fertige Bundle geladen: ./install.sh --offline
#
# Weil die Verwechslung teuer ist (30 Sekunden Timeout, dann eine kryptische
# Meldung über auth.docker.io), wird sie hier vorab abgefangen.
# -----------------------------------------------------------------------------
echo "[0/3] Prüfe Internetzugang (dieses Skript braucht ihn)..."
# KEIN -f: auth.docker.io antwortet auf ein nacktes GET mit 404 – das ist trotzdem eine
# Antwort und beweist Erreichbarkeit. -f würde den 404 als Fehler werten und auf einer
# völlig intakten Internet-Verbindung fälschlich abbrechen. Ohne -f liefert curl nur bei
# echten Verbindungsproblemen (Timeout/DNS/refused) einen Fehlercode.
if ! curl -sS --max-time 8 -o /dev/null https://auth.docker.io 2>/dev/null; then
    echo ""
    echo "FEHLER: Docker Hub ist von dieser Maschine aus nicht erreichbar."
    echo ""
    echo "Dieses Skript baut die Images und lädt die Basis-Images – dafür braucht es"
    echo "Internet. Es gehört auf eine Maschine MIT Internetzugang, nicht auf die"
    echo "abgeschottete Ziel-VM."
    echo ""
    echo "Richtiger Ablauf:"
    echo "  1. Auf einer Maschine MIT Internet (z.B. dem Entwicklungsserver):"
    echo "       ./docker/scripts/build-offline-bundle.sh"
    echo "     -> erzeugt flvs-images.tar (ca. 400 MB)"
    echo "  2. Repository UND flvs-images.tar auf die Ziel-VM kopieren,"
    echo "     z.B. nach /opt/flvs/ und /opt/flvs/flvs-images.tar"
    echo "  3. Auf der Ziel-VM – hier wird NICHT gebaut:"
    echo "       cd /opt/flvs && ./install.sh --offline"
    echo ""
    exit 1
fi
echo "      Docker Hub erreichbar."

# docker compose build wertet die ganze Datei aus; Pflicht-Variablen mit
# :? würden sonst abbrechen -> Dummy-Werte reichen für den reinen Build.
export SECRET_KEY="${SECRET_KEY:-build-dummy-secret}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-build-dummy-pass}"

echo "[1/3] Baue Anwendungs-Images (web, celery-worker, celery-beat)..."
docker compose build

echo "[2/3] Lade Basis-Images..."
for img in $BASE_IMAGES; do
    docker pull "$img"
done

echo "[3/3] Exportiere alle Images nach $OUT ..."
# shellcheck disable=SC2086
docker save $APP_IMAGES $BASE_IMAGES -o "$OUT"

echo ""
echo "Fertig: $OUT ($(du -h "$OUT" | cut -f1))"
echo ""
echo "Nächste Schritte:"
echo "  1. Repository UND $OUT auf die Ziel-VM kopieren"
echo "     (z.B. nach /opt/flvs/ und /opt/flvs/flvs-images.tar)"
echo "  2. Auf der VM:  cd /opt/flvs && ./install.sh --offline"
