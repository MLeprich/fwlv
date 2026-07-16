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
section "3b. Port 443 im Detail"
# Welcher Modus ist konfiguriert?
CONF443="docker/nginx/conf.d/https-internal.conf"
if [[ -f "$CONF443" ]]; then
    if grep -qE 'listen 443 ssl' "$CONF443"; then MODE443="tls"; else MODE443="plain"; fi
    echo "  Konfiguriert: $MODE443  ($CONF443)"
else
    MODE443="aus"
    echo "  KEINE 443-Konfiguration vorhanden – nginx lauscht im Container nur auf 80."
    echo "  (Der Host-Port 443 ist trotzdem offen: docker-proxy nimmt an, im Container"
    echo "   verweigert dann aber niemand -> genau das ergibt 'connection refused'.)"
    echo "  Aktivieren: ./docker/scripts/enable-internal-https.sh --plain"
fi

# Lauscht der LAUFENDE nginx wirklich auf 443? (nginx -T zeigt die geladene Konfig –
# eine Datei auf der Platte nützt nichts, wenn nginx nie neu geladen wurde)
echo "  listen-Direktiven im laufenden nginx:"
listen_zeilen=$(docker compose exec -T nginx nginx -T 2>/dev/null | grep -E '^\s*listen' | sort -u)
[[ -n "$listen_zeilen" ]] && echo "$listen_zeilen" | sed 's/^/    /' || echo "    nginx-Container nicht erreichbar."
if [[ "$MODE443" != "aus" ]]; then
    if ! docker compose exec -T nginx nginx -T 2>/dev/null | grep -qE '^\s*listen 443'; then
        echo "    !! 443 ist konfiguriert, aber der laufende nginx kennt es NICHT."
        echo "    !! -> docker compose restart nginx"
    fi
fi

# Beide Protokolle real antesten – die Kombination verrät den Zustand
pc=$(curl -s  -o /dev/null -w '%{http_code}' --max-time 5 http://localhost:443/  2>/dev/null); pc=${pc:-000}
tc=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 5 https://localhost:443/ 2>/dev/null); tc=${tc:-000}
echo "  Klartext-HTTP gegen 443:  $pc"
echo "  TLS gegen 443:            $tc"
case "$MODE443" in
    plain)
        [[ "$pc" == 2* || "$pc" == 3* ]] \
            && echo "  => Klartext OK. Der Proxy muss Protokoll HTTP (nicht HTTPS) zum Backend sprechen." \
            || echo "  => Klartext antwortet NICHT – nginx-Log unten prüfen (Abschnitt 8) und ggf. restart." ;;
    tls)
        [[ "$tc" == 2* || "$tc" == 3* ]] \
            && echo "  => TLS OK. Der Proxy muss HTTPS zum Backend sprechen." \
            || echo "  => TLS antwortet NICHT – Zertifikat/Config prüfen (Abschnitt 8)." ;;
esac

# Spricht der Proxy das falsche Protokoll? TLS-Handshakes auf einem Klartext-Port
# hinterlassen \x16\x03... im Access-Log.
if docker compose logs --tail=200 nginx 2>/dev/null | grep -q 'x16.x03'; then
    echo "  !! Im Log stehen TLS-Handshake-Bytes (\\x16\\x03...) auf dem Klartext-Port:"
    echo "  !! Der Proxy spricht HTTPS, nginx erwartet dort HTTP. Entweder Proxy auf"
    echo "  !! Protokoll HTTP stellen oder TLS aktivieren (--csr/--cert/--self-signed)."
fi

# localhost sagt nichts über den Weg von außen: gegen die eigene externe IP testen.
# Geht localhost, aber die IP nicht, blockt eine Firewall auf der VM.
VM_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [[ -n "$VM_IP" ]]; then
    ic=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://$VM_IP:443/" 2>/dev/null); ic=${ic:-000}
    echo "  Klartext gegen die VM-IP ($VM_IP:443): $ic"
    if [[ ( "$pc" == 2* || "$pc" == 3* ) && "$ic" == 000 ]]; then
        echo "  !! localhost geht, die eigene IP nicht -> Host-Firewall blockt 443 von außen."
        echo "  !! Prüfen: ufw status / nft list ruleset / iptables -S | grep 443"
    fi
fi
command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | head -6 | sed 's/^/  ufw: /'

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
