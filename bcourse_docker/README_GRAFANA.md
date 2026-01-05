# Grafana Configuration Guide

**⚠️ Grafana has been moved to a separate server.**

Grafana is now hosted at: **https://grafana-upstream:3000**

Access via redirect: **https://grafana.example.com** (redirects to grafana-upstream:3000)

## Redirect Configuration

The `grafana.example.com` domain is configured in `docker-compose.yml` to redirect to the new Grafana server:

```yaml
grafana-redirect:
  image: "traefik/whoami:latest"
  container_name: "grafana-redirect"
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.grafana-redirect.rule=Host(`grafana.example.com`)"
    - "traefik.http.routers.grafana-redirect.entrypoints=websecure"
    - "traefik.http.routers.grafana-redirect.tls.certresolver=${TRAEFIK_CERT_RESOLVER:-myresolver}"
    - "traefik.http.middlewares.grafana-redirect.redirectregex.regex=^https://grafana\\.example\\.com(.*)"
    - "traefik.http.middlewares.grafana-redirect.redirectregex.replacement=https://grafana-upstream:3000$$1"
    - "traefik.http.middlewares.grafana-redirect.redirectregex.permanent=true"
    - "traefik.http.routers.grafana-redirect.middlewares=grafana-redirect"
    - "traefik.http.services.grafana-redirect.loadbalancer.server.port=80"
    - "traefik.docker.network=web-network"
  networks:
    - web-network
  restart: unless-stopped
```

This ensures that:
- `https://grafana.example.com` redirects to `https://grafana-upstream:3000` while preserving the path
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
