#!/bin/bash
# =============================================================================
# FLVS - SSL Certificate Initialization (Let's Encrypt)
# =============================================================================

DOMAIN="${1:-your-domain.de}"
EMAIL="${2:-admin@your-domain.de}"

# Check if certificates already exist
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "Certificates already exist for $DOMAIN"
    exit 0
fi

echo "Obtaining SSL certificate for $DOMAIN..."

# Create temporary nginx config for ACME challenge
docker compose up -d nginx

# Wait for nginx to start
sleep 5

# Run certbot
docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN"

# Reload nginx with SSL config
docker compose exec nginx nginx -s reload

echo "SSL certificate obtained successfully!"
echo "Now enable HTTPS in docker/nginx/conf.d/default.conf"
