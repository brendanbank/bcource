# Grafana Configuration Guide

**⚠️ Grafana has been moved to a separate server.**

Grafana is now hosted at: **https://srv6.bgwlan.nl:3000**

Access via redirect: **https://grafana.brendanbank.com** (redirects to srv6.bgwlan.nl:3000)

## Redirect Configuration

The `grafana.brendanbank.com` domain is configured in `docker-compose.yml` to redirect to the new Grafana server:

```yaml
grafana-redirect:
  image: "traefik/whoami:latest"
  container_name: "grafana-redirect"
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.grafana-redirect.rule=Host(`grafana.brendanbank.com`)"
    - "traefik.http.routers.grafana-redirect.entrypoints=websecure"
    - "traefik.http.routers.grafana-redirect.tls.certresolver=${TRAEFIK_CERT_RESOLVER:-myresolver}"
    - "traefik.http.middlewares.grafana-redirect.redirectregex.regex=^https://grafana\\.brendanbank\\.com(.*)"
    - "traefik.http.middlewares.grafana-redirect.redirectregex.replacement=https://srv6.bgwlan.nl:3000$$1"
    - "traefik.http.middlewares.grafana-redirect.redirectregex.permanent=true"
    - "traefik.http.routers.grafana-redirect.middlewares=grafana-redirect"
    - "traefik.http.services.grafana-redirect.loadbalancer.server.port=80"
    - "traefik.docker.network=web-network"
  networks:
    - web-network
  restart: unless-stopped
```

This ensures that:
- `https://grafana.brendanbank.com` redirects to `https://srv6.bgwlan.nl:3000` while preserving the path
- HTTP requests are automatically redirected to HTTPS (via Traefik's global redirect)
- The redirect is permanent (301), which helps with SEO and browser caching

## Management

To restart the redirect service:

```bash
cd bcourse_docker
docker compose restart grafana-redirect
```

To view logs:

```bash
docker compose logs grafana-redirect
```
