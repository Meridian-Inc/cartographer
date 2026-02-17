# ─────────────────────────────────────────────────────────────────────────────
# Cartographer Nginx - TLS Termination Proxy
# ─────────────────────────────────────────────────────────────────────────────
#
# TLS certificate resolution order:
#   1. Let's Encrypt certs at /etc/letsencrypt/live/<domain>/
#   2. Self-signed fallback at /etc/nginx/ssl/ (testing only)
#
# The entrypoint script symlinks the best available certificate to
# /etc/nginx/ssl/ so nginx.conf always reads from a single path.
# ─────────────────────────────────────────────────────────────────────────────

FROM nginx:1.25-alpine

# Install openssl for self-signed cert generation
RUN apk add --no-cache openssl

# Create directories for certificates and ACME challenges
RUN mkdir -p /etc/nginx/ssl /var/www/certbot

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy entrypoint script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Generate self-signed certificate as fallback for initial startup
# This allows the container to start before Let's Encrypt certs are obtained
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/privkey.pem \
    -out /etc/nginx/ssl/fullchain.pem \
    -subj "/CN=localhost" \
    && chmod 600 /etc/nginx/ssl/privkey.pem

# Expose HTTP and HTTPS ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/healthz || exit 1

# Entrypoint resolves cert paths, then starts nginx
ENTRYPOINT ["/docker-entrypoint.sh"]
