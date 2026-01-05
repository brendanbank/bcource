# Grafana Configuration Guide

**⚠️ Grafana has been moved to a separate server.**

Grafana is now hosted at: **https://srv6.bgwlan.nl:3000** (HTTPS for encrypted connections)

Access via proxy: **https://grafana.brendanbank.com** (proxies to srv6.bgwlan.nl:3000)

## Proxy Configuration

The `grafana.brendanbank.com` domain is configured using an nginx proxy container that forwards requests to the external Grafana server. This means the URL stays as `grafana.brendanbank.com` in the browser.

### Architecture

```
Client → Traefik (HTTPS) → nginx-proxy (HTTP) → Grafana (HTTPS)
```

### Docker Compose Configuration

The `grafana-proxy` service uses nginx to proxy requests:

```yaml
grafana-proxy:
  image: "nginx:alpine"
  container_name: "grafana-proxy"
  volumes:
    - "./grafana/nginx-proxy.conf:/etc/nginx/conf.d/default.conf:ro"
  labels:
    - "traefik.http.routers.grafana-proxy.rule=Host(`grafana.brendanbank.com`)"
    - "traefik.http.routers.grafana-proxy.entrypoints=websecure"
    - "traefik.http.routers.grafana-proxy.tls.certresolver=myresolver"
```

### Nginx Proxy Configuration

The nginx configuration (`grafana/nginx-proxy.conf`) proxies all requests to `https://srv6.bgwlan.nl:3000` while:
- Preserving the original host header (`grafana.brendanbank.com`)
- Forwarding client IP addresses and headers
- Supporting WebSocket connections (for Grafana live features)
- Disabling SSL verification (`proxy_ssl_verify off`) for self-signed certificates
- Setting timeouts to 300s for long-running requests
- Handling streaming responses properly

This configuration:
- Routes requests for `grafana.brendanbank.com` to the external Grafana server
- Uses automatic SSL certificate management via Let's Encrypt for the frontend (Traefik)
- Connects to Grafana over HTTPS for encrypted connections (passwords are encrypted in transit)
- Disables SSL certificate verification since Grafana uses a self-signed certificate

## Management

To restart the proxy service:

```bash
cd bcourse_docker
docker compose restart grafana-proxy
```

To reload nginx configuration (after editing `grafana/nginx-proxy.conf`):

```bash
docker compose exec grafana-proxy nginx -s reload
```

To view proxy logs:

```bash
docker compose logs grafana-proxy
```

To view Traefik logs:

```bash
docker compose logs traefik | grep grafana
```

## Troubleshooting

### Redirect Issues

If you're being redirected to `srv6.bgwlan.nl` instead of staying on `grafana.brendanbank.com`:

1. **Clear browser cache** - This is often the cause. Use incognito/private mode or clear cache for the site.

2. **Check Grafana configuration** on srv6 - Ensure `grafana.ini` has:
   ```ini
   [server]
   root_url = https://grafana.brendanbank.com/
   domain = grafana.brendanbank.com
   enforce_domain = false
   ```

3. **Test the proxy:**
   ```bash
   curl -I https://grafana.brendanbank.com
   ```

### Connection Issues

If you experience timeouts or connection errors:

1. **Check container status:**
   ```bash
   docker compose ps grafana-proxy
   ```

2. **Check logs:**
   ```bash
   docker compose logs grafana-proxy
   docker compose logs traefik | grep grafana
   ```

3. **Test connectivity:**
   ```bash
   curl -k https://srv6.bgwlan.nl:3000/api/health
   ```

4. **Reload nginx configuration:**
   ```bash
   docker compose exec grafana-proxy nginx -s reload
   ```
