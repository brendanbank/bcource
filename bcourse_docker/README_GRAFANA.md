# Grafana Configuration Guide

**⚠️ Grafana has been moved to a separate server.**

Grafana is now hosted at: **https://grafana-upstream:3000**

Access via proxy: **https://grafana.example.com** (proxies to grafana-upstream:3000)

## Proxy Configuration

The `grafana.example.com` domain is configured using Traefik's file provider to proxy requests directly to the external Grafana server. This means the URL stays as `grafana.example.com` in the browser.

### Traefik File Provider Configuration

Traefik is configured with a file provider that watches `traefik/dynamic/` for configuration files. The Grafana proxy is defined in `traefik/dynamic/grafana.yml`:

```yaml
http:
  routers:
    grafana:
      rule: "Host(`grafana.example.com`)"
      service: grafana-service
      entryPoints:
        - websecure
      tls:
        certResolver: myresolver

  services:
    grafana-service:
      loadBalancer:
        servers:
          - url: "https://grafana-upstream:3000"
        passHostHeader: true
```

This configuration:
- Routes requests for `grafana.example.com` to the external Grafana server
- Preserves the original host header (`passHostHeader: true`)
- Uses automatic SSL certificate management via Let's Encrypt
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

If the proxy isn't working:

1. **Check Traefik configuration:**
   ```bash
   docker compose exec traefik traefik version
   docker compose logs traefik | grep -i "file\|grafana"
   ```

2. **Verify the configuration file exists:**
   ```bash
   cat bcourse_docker/traefik/dynamic/grafana.yml
   ```

3. **Test connectivity from Traefik container:**
   ```bash
   docker compose exec traefik wget -O- --no-check-certificate https://grafana-upstream:3000
   ```

4. **Check Traefik dashboard:**
   Visit `http://localhost:8080` (or your `TRAEFIK_DASHBOARD_PORT`) to see if the Grafana router and service are registered.
