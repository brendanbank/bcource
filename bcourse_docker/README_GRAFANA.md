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

### TLS Handshake Errors on Grafana Server

If you see errors like `tls: unknown certificate` in Grafana logs on srv6:

**The issue:** Grafana is rejecting TLS connections from Traefik. This is usually because Grafana is configured to require client certificates or has strict TLS validation.

**Solution:** Configure Grafana on srv6 to accept connections from Traefik:

1. **Check Grafana's TLS configuration** in `grafana.ini`:
   ```ini
   [server]
   protocol = https
   cert_file = /path/to/cert.pem
   cert_key = /path/to/key.pem
   
   # Make sure these are NOT set (they enable mutual TLS):
   # client_auth = require
   # client_ca = /path/to/ca.pem
   ```

2. **If Grafana requires client certificates**, you have two options:
   - **Option A (Recommended):** Disable client certificate requirement in Grafana's config
   - **Option B:** Configure Traefik to present a client certificate (more complex)

3. **Verify Grafana accepts connections:**
   ```bash
   # From Traefik server, test connection
   curl -k https://srv6.bgwlan.nl:3000
   ```

### Gateway Timeout / Client Timeouts

If you get timeout errors:

1. **Test connectivity from Traefik container:**
   ```bash
   # Test if Traefik can reach Grafana
   docker compose exec traefik wget -O- --no-check-certificate --timeout=10 https://srv6.bgwlan.nl:3000
   ```

2. **Check Traefik logs for errors:**
   ```bash
   docker compose logs traefik | grep -i "grafana\|timeout\|error\|handshake"
   ```

3. **Verify backend is accessible from host:**
   ```bash
   # From the host machine
   curl -k --max-time 10 https://srv6.bgwlan.nl:3000
   ```

4. **Check Grafana health endpoint:**
   ```bash
   curl -k https://srv6.bgwlan.nl:3000/api/health
   ```

5. **Check Traefik dashboard:**
   Visit `http://localhost:8080` (or your `TRAEFIK_DASHBOARD_PORT`) to see if the Grafana router and service are registered correctly.

6. **Verify timeout settings:**
   The configuration includes:
   - Entrypoint timeouts: 300s (read/write/idle)
   - Health check: 30s interval, 10s timeout
   - These can be adjusted in `docker-compose.yml` and `traefik/dynamic/grafana.yml` if needed

7. **If SSL verification is needed:**
   Edit `traefik/dynamic/grafana.yml` and comment out the `serversTransport` section:
   ```yaml
   # serversTransports:
   #   grafana-transport:
   #     insecureSkipVerify: true
   ```

### Other Issues

1. **Check Traefik configuration:**
   ```bash
   docker compose exec traefik traefik version
   docker compose logs traefik | grep -i "file\|grafana"
   ```

2. **Verify the nginx configuration:**
   ```bash
   docker compose exec grafana-proxy nginx -t
   cat bcourse_docker/grafana/nginx-proxy.conf
   ```

3. **Reload nginx:**
   ```bash
   docker compose exec grafana-proxy nginx -s reload
   ```

4. **Restart the proxy:**
   ```bash
   docker compose restart grafana-proxy
   ```
