#!/bin/sh
set -e

CERT_DIR="/etc/nginx/ssl"
LE_DIR="/etc/letsencrypt/live"

# Find Let's Encrypt certificates (use DOMAIN env var or auto-detect)
resolve_letsencrypt_certs() {
    if [ -n "$DOMAIN" ] && [ -d "$LE_DIR/$DOMAIN" ]; then
        echo "$LE_DIR/$DOMAIN/"
        return
    fi

    # Auto-detect: use the first domain directory found
    for dir in "$LE_DIR"/*/; do
        if [ -f "${dir}fullchain.pem" ]; then
            echo "$dir"
            return
        fi
    done
}

LE_CERT_DIR=$(resolve_letsencrypt_certs)

if [ -n "$LE_CERT_DIR" ]; then
    echo "Using Let's Encrypt certificates from: $LE_CERT_DIR"
    # Symlink Let's Encrypt certs to the path nginx.conf expects
    ln -sf "${LE_CERT_DIR}fullchain.pem" "$CERT_DIR/fullchain.pem"
    ln -sf "${LE_CERT_DIR}privkey.pem" "$CERT_DIR/privkey.pem"
else
    echo "No Let's Encrypt certificates found. Using self-signed certificate."
    echo "To use Let's Encrypt, run: docker compose -f docker-compose.prod.yml run --rm certbot certonly --webroot -w /var/www/certbot -d yourdomain.com"
fi

# Start a background process that watches for cert renewals and reloads nginx
(
    while true; do
        # inotifywait is not available in alpine by default, so poll instead
        sleep 12h
        # Re-resolve in case certs were just created
        LE_CERT_DIR=$(resolve_letsencrypt_certs)
        if [ -n "$LE_CERT_DIR" ]; then
            ln -sf "${LE_CERT_DIR}fullchain.pem" "$CERT_DIR/fullchain.pem"
            ln -sf "${LE_CERT_DIR}privkey.pem" "$CERT_DIR/privkey.pem"
            echo "Reloading nginx for certificate update..."
            nginx -s reload
        fi
    done
) &

exec nginx -g "daemon off;"
