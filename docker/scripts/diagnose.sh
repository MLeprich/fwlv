#!/bin/bash
# =============================================================================
# FLVS - Ein-Klick-Diagnose bei Zugriffsproblemen (400/403/502 usw.)
# =============================================================================
# Sammelt alles, was zur Eingrenzung eines Zugriffsproblems nötig ist, in einer
# Ausgabe – damit man sie einmal kopieren und weitergeben kann, statt sich durch
# einzelne Befehle zu fragen.
#
#   cd /opt/flvs && ./docker/scripts/diagnose.sh
#
# Optional: die extern aufgerufene URL mitgeben, dann wird auch der Weg von außen
# getestet:
#   ./docker/scripts/diagnose.sh https://fwlager.rz.oberhausen.de/
# =============================================================================

cd "$(dirname "$0")/../.." || exit 1

EXTERNAL_URL="$1"
LINE="────────────────────────────────────────────────────────────────────"

section() { echo; echo "$LINE"; echo "  $1"; echo "$LINE"; }

echo "FLVS-Diagnose  $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "Host: $(hostname)   Verzeichnis: $(pwd)"

# ---------------------------------------------------------------------------
section "1. Container-Status"
docker compose ps 2>&1

# ---------------------------------------------------------------------------
section "2. Konfiguration (.env, gekürzt)"
if [[ -f .env ]]; then
    grep -E '^(ALLOWED_HOSTS|DOMAIN|USE_SSL|TRUST_PROXY_SSL_HEADER|CSRF_TRUSTED|HTTP_PORT|HTTPS_PORT)=' .env
else
    echo "  KEINE .env gefunden!"
fi

# ---------------------------------------------------------------------------
section "3. Lauscht nginx? (Ports auf dem Host)"
{ ss -ltnp 2>/dev/null || netstat -ltnp 2>/dev/null; } | grep -E ':(80|443)\b' || echo "  Nichts auf 80/443 – lauscht der nginx-Container?"

# ---------------------------------------------------------------------------
section "4. Zugriff INTERN testen (an nginx vorbei am Proxy)"
echo "  Erwartung: überall 200 oder 302. Ein 400 hier => das Problem liegt im Stack,"
echo "  nicht am vorgelagerten Proxy."
DOMAIN_ENV=$(grep -E '^DOMAIN=' .env 2>/dev/null | cut -d= -f2)
for host in "$DOMAIN_ENV" localhost 127.0.0.1; do
    [[ -z "$host" ]] && continue
    code=$(curl -s -o /dev/null -w "%{http_code}" -H "Host: $host" http://localhost/ 2>/dev/null)
    printf "  Host: %-34s -> HTTP %s\n" "$host" "$code"
done

# ---------------------------------------------------------------------------
section "5. Große Header simulieren (SSO-Proxy-Verdacht)"
echo "  Ein Firmen-Proxy mit SSO hängt große Header an. Wird nginx' Puffer überschritten,"
echo "  antwortet er mit 400 – ohne dass Django den Request je sieht."
big=$(head -c 20000 < /dev/zero | tr '\0' 'x')
code=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Test-Big: $big" http://localhost/ 2>/dev/null)
echo "  Request mit ~20 KB Header -> HTTP $code   (400 = Puffer zu klein, siehe Abschnitt 8)"

# ---------------------------------------------------------------------------
if [[ -n "$EXTERNAL_URL" ]]; then
    section "6. Zugriff VON AUSSEN testen ($EXTERNAL_URL)"
    curl -sk -o /dev/null -w "  HTTP %{http_code}  |  Umleitung: %{redirect_url}\n" "$EXTERNAL_URL" 2>&1
    echo "  Header:"
    curl -skI "$EXTERNAL_URL" 2>&1 | sed 's/^/    /' | head -15
else
    section "6. Zugriff von außen"
    echo "  Übersprungen. Zum Testen die externe URL mitgeben:"
    echo "    ./docker/scripts/diagnose.sh https://fwlager.rz.oberhausen.de/"
fi

# ---------------------------------------------------------------------------
section "7. nginx – letzte Zugriffe (host=... zeigt den durchgereichten Host-Header)"
docker compose logs --tail=15 nginx 2>&1 | grep -E 'host=|GET |POST ' | tail -15 \
    || echo "  Keine Zugriffe protokolliert."

# ---------------------------------------------------------------------------
section "8. nginx – letzte FEHLER (Grund für einen 400 steht hier im Klartext)"
echo "  Achte auf: 'client sent too long header', 'client sent invalid header',"
echo "  'client exceeded ... buffer', 'upstream'."
docker compose exec -T nginx sh -c 'tail -25 /var/log/nginx/error.log' 2>/dev/null \
    || docker compose logs --tail=25 nginx 2>&1 | grep -iE 'error|warn|\[crit' \
    || echo "  Kein error.log lesbar."

# ---------------------------------------------------------------------------
section "9. Django – abgelehnte Hosts (DisallowedHost)"
docker compose exec -T web sh -c "grep -oh \"Invalid HTTP_HOST header: '[^']*'\" /app/logs/security.log 2>/dev/null | sort | uniq -c | sort -rn" 2>/dev/null \
    | grep . || echo "  Keine – Django hat keinen Request wegen des Hosts abgelehnt."
echo "  (Ein leeres Ergebnis bei gleichzeitigem 400 => der 400 kommt von nginx, nicht von Django.)"

# ---------------------------------------------------------------------------
section "10. Django – letzte Anwendungsfehler"
docker compose logs --tail=20 web 2>&1 | grep -iE 'error|traceback|exception|warning' | tail -12 \
    || echo "  Keine auffälligen Meldungen."

echo
echo "$LINE"
echo "  Fertig. Diese Ausgabe komplett kopieren und weitergeben."
echo "$LINE"
