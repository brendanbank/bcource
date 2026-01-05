# Grafana Configuration Guide

**⚠️ Grafana has been moved to a separate server.**

Grafana is now hosted at: **https://srv6.bgwlan.nl:3000**

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
```

This configuration:
- Routes requests for `grafana.brendanbank.com` to the external Grafana server
- Preserves the original host header (`passHostHeader: true`)
- Uses automatic SSL certificate management via Let's Encrypt for the frontend
- Disables SSL verification for the backend (`insecureSkipVerify: true`) since the backend uses an invalid certificate
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

### Gateway Timeout

If you get a Gateway Timeout error:

1. **Check if SSL verification is the issue:**
   The configuration has `insecureSkipVerify: true` enabled by default. If you're still getting timeouts, verify:
   ```bash
   # Test connectivity from Traefik container
   docker compose exec traefik wget -O- --no-check-certificate https://srv6.bgwlan.nl:3000
   ```

2. **Check Traefik logs:**
   ```bash
   docker compose logs traefik | grep -i "grafana\|timeout\|error"
   ```

3. **Verify backend is accessible:**
   ```bash
   # From the host machine
   curl -k https://srv6.bgwlan.nl:3000
   ```

4. **Check Traefik dashboard:**
   Visit `http://localhost:8080` (or your `TRAEFIK_DASHBOARD_PORT`) to see if the Grafana router and service are registered correctly.

5. **If SSL verification is needed:**
   Edit `traefik/dynamic/grafana.yml` and comment out the `serverTransport` section:
   ```yaml
   # serverTransport:
   #   insecureSkipVerify: true
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
