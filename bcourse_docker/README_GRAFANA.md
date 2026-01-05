# Grafana Configuration Guide

**⚠️ Grafana has been moved to a separate server.**

Grafana is now hosted at: **https://srv6.bgwlan.nl:3000** (HTTPS for encrypted connections)

Access via proxy: **https://grafana.brendanbank.com** (proxies to srv6.bgwlan.nl:3000)

## Proxy Configuration

The `grafana.brendanbank.com` domain is configured using Traefik's file provider to proxy requests directly to the external Grafana server. This means the URL stays as `grafana.brendanbank.com` in the browser.

### Traefik File Provider Configuration

Traefik is configured with a file provider that watches `traefik/dynamic/` for configuration files. The Grafana proxy is defined in `traefik/dynamic/grafana.yml`:

```yaml
http:
  routers:
    grafana:
      rule: "Host(`grafana.brendanbank.com`)"
      service: grafana-service
      entryPoints:
        - websecure
      tls:
        certResolver: myresolver

  services:
    grafana-service:
      loadBalancer:
        servers:
          - url: "https://srv6.bgwlan.nl:3000"
        passHostHeader: true
        serversTransport: grafana-transport

  serversTransports:
    grafana-transport:
      insecureSkipVerify: true
```

This configuration:
- Routes requests for `grafana.brendanbank.com` to the external Grafana server
- Preserves the original host header (`passHostHeader: true`)
- Uses automatic SSL certificate management via Let's Encrypt for the frontend
- Connects to Grafana over HTTPS for encrypted connections (passwords are encrypted in transit)
- Disables SSL certificate verification (`insecureSkipVerify: true`) since Grafana uses a self-signed certificate
- Automatically watches for configuration changes

### Docker Compose Changes

Traefik has been configured with:
- File provider enabled: `--providers.file.directory=/etc/traefik/dynamic`
- File watching enabled: `--providers.file.watch=true`
- Volume mount: `./traefik/dynamic:/etc/traefik/dynamic:ro`

## Management

To reload Traefik configuration (after editing `traefik/dynamic/grafana.yml`):

```bash
cd bcourse_docker
docker compose restart traefik
```

Or Traefik will automatically reload when files change (file watching is enabled).

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

2. **Verify the configuration file exists:**
   ```bash
   cat bcourse_docker/traefik/dynamic/grafana.yml
   ```

3. **Reload Traefik:**
   ```bash
   docker compose restart traefik
   ```
