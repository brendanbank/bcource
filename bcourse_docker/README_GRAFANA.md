# Grafana Configuration Guide

Grafana is deployed as a separate service with **network isolation** for security. It runs on its own Docker network (`grafana-network`) and **cannot access the database** or other application services. Access is provided through Traefik reverse proxy with automatic SSL certificate management via Let's Encrypt.

## Quick Start

```bash
cd bcourse_docker
mkdir -p grafana/data
chmod 777 grafana/data
docker compose up -d grafana
```

Access at: https://grafana.brendanbank.com

## Configuration

### Environment Variables (`.env`)

```bash
# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password_here
GRAFANA_PLUGINS=grafana-clock-panel,grafana-piechart-panel

# SMTP Configuration
GRAFANA_SMTP_HOST=172.17.0.1:25  # or host.docker.internal:25 (port included in host)

# Optional: Traefik Certificate Resolver
TRAEFIK_CERT_RESOLVER=myresolver
```

### Directory Structure

```
bcourse_docker/
├── grafana/
│   ├── grafana.ini          # Configuration file
│   ├── data/                # Persistent storage
│   └── provisioning/        # Provisioning configs
└── docker-compose.yml
```

## Network Isolation

Grafana runs on `grafana-network` (isolated from `web-network`):
- ✅ Can access: Traefik, host via `host.docker.internal`
- ❌ Cannot access: MySQL, bcourse, or any `web-network` services

```
┌─────────┐
│ Traefik │ ← On both networks
└────┬────┘
  ┌──┴──┐
┌─▼─┐ ┌─▼──────┐
│web│ │grafana│
└─┬─┘ └─┬──────┘
┌─▼─┐ ┌─▼──────┐
│DB │ │Grafana │
└───┘ └────────┘
```

## Authentication

### Default Login
- **Username:** `admin` (or `GRAFANA_ADMIN_USER`)
- **Password:** `GRAFANA_ADMIN_PASSWORD` from `.env`

### Invite-Only Sign-Up (Current Setup)
- Open registration is disabled (`allow_sign_up = false`)
- Only invited users can create accounts
- Admin sends invites: **Administration** → **Users and access** → **Users** → **Invite user**

### Google OAuth (Disabled)
Currently disabled. To enable:
1. Get credentials from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Add to `.env`:
   ```bash
   GRAFANA_GOOGLE_CLIENT_ID=your_client_id
   GRAFANA_GOOGLE_CLIENT_SECRET=your_secret
   ```
3. Uncomment `[auth.google]` section in `grafana.ini`
4. Restart: `docker compose restart grafana`

## Plugins

### Install via Environment Variable (Recommended)

Add to `.env`:
```bash
GRAFANA_PLUGINS=grafana-clock-panel,grafana-piechart-panel,grafana-worldmap-panel
```

Restart: `docker compose restart grafana`

### Manual Installation

```bash
docker compose exec grafana grafana-cli plugins install <plugin-id>
docker compose restart grafana
```

### Popular Plugins

**Panels:** `grafana-clock-panel`, `grafana-piechart-panel`, `grafana-worldmap-panel`, `grafana-polystat-panel`  
**Data Sources:** `grafana-simple-json-datasource`, `grafana-influxdb-datasource`, `grafana-prometheus-datasource`  
**Apps:** `grafana-kubernetes-app`, `grafana-zabbix-app`

**Catalog:** https://grafana.com/grafana/plugins/

### Management Commands

```bash
docker compose exec grafana grafana-cli plugins ls              # List installed
docker compose exec grafana grafana-cli plugins list-remote    # List available
docker compose exec grafana grafana-cli plugins update-all      # Update all
docker compose exec grafana grafana-cli plugins remove <id>    # Remove
```

## Alerting

### Quick Start

1. **Access:** **Alerts & IRM** → **Alerting**
2. **Create Contact Point:** **Alerting** → **Contact points** → **+ Add contact point**
   - Email (already configured via SMTP)
   - Pushover (recommended for mobile push notifications)
   - Telegram, Slack, Webhook, etc.
3. **Create Alert Rule:** **Alerting** → **Alert rules** → **+ New alert rule**
   - Define query from your data source
   - Set conditions (e.g., value > threshold)
   - Configure summary and notifications

### Alert Templates

**⚠️ IMPORTANT:** Two different template contexts:

1. **Alert Rule Summary** - Use `$labels` and `$values` (single alert)
2. **Notification Template** - Use `.Alerts`, `.Labels`, `.Values` (multiple alerts)

#### Alert Rule Summary Templates

**For Summary field (single alert):**
```
🚨 {{ index $labels "name" }} is DOWN

Site: {{ index $labels "site_name" }}
Type: {{ index $labels "type" }}
Instance: {{ index $labels "instance" }}
```

**With uptime:**
```
Unifi Device "{{ index $labels "name" }}" on {{ index $labels "site_name" }} has an uptime of {{ humanizeDuration (index $values "A").Value }}
```

**Available variables:**
- `{{ index $labels "name" }}` or `{{ $labels.name }}` - Label values
- `{{ (index $values "A").Value }}` or `{{ $values.A.Value }}` - Query result
- `{{ humanizeDuration $values.A.Value }}` - Human-readable duration
- `{{ humanize $values.A.Value }}` - Human-readable number

#### Notification Templates

**For Contact Points → Edit → Message (multiple alerts):**
```
{{ range .Alerts }}
{{ if eq .Values.A.Value 0 }}
🚨 {{ .Labels.name }} is DOWN
Site: {{ .Labels.site_name }}
Type: {{ .Labels.type }}
{{ end }}
{{ end }}
```

**Grouped template:**
```
{{ $hasDown := false }}
{{ range .Alerts }}
{{ if eq .Values.A.Value 0 }}
{{ $hasDown = true }}
{{ end }}
{{ end }}
{{ if $hasDown }}
🚨 Access Point(s) Down:

{{ range .Alerts }}
{{ if eq .Values.A.Value 0 }}
• {{ .Labels.name }} ({{ .Labels.type }}) at {{ .Labels.site_name }}
{{ end }}
{{ end }}
{{ end }}
```

### Mobile Push Notifications

**Pushover (Recommended):**
1. Sign up at https://pushover.net
2. Install app and get User Key + API Token
3. In Grafana: **Alerting** → **Contact points** → **+ Add contact point** → **Pushover**

**Other options:** Telegram, Slack (with mobile app), PagerDuty, OpsGenie

### Do You Need Alertmanager?

**No.** Grafana Alerting is self-contained and doesn't require Prometheus Alertmanager. It handles alert evaluation, routing, grouping, and notifications.

## Grafana OnCall (Optional)

**⚠️ Requires Backend:** OnCall needs either Grafana Cloud OnCall or a self-hosted backend (PostgreSQL + Redis + OnCall engine).

**Recommendation:** Use built-in Grafana Alerting instead (no backend required).

If you need OnCall:
1. **Grafana Cloud:** Get OnCall URL and Stack ID, update `grafana/provisioning/plugins/oncall.yaml`
2. **Self-Hosted:** See [OnCall Documentation](https://grafana.com/docs/oncall/latest/open-source/) [Deprecated in the summer of 2025]

## Data Persistence

Data stored in `./grafana/data/`:
- Dashboards, data sources, users, plugins, SQLite database

**Backup:**
```bash
tar -czf grafana-backup-$(date +%Y%m%d).tar.gz grafana/data/
```

## Troubleshooting

### Container Won't Start
```bash
docker compose logs grafana
ls -la grafana/data  # Check permissions (should be writable)
```

### Traefik Can't Route
```bash
docker compose ps grafana
docker compose logs traefik | grep grafana
docker compose exec traefik ping grafana
```

### SMTP Connection Issues

**Error:** `dial tcp 172.17.0.1:25: connect: connection refused`

**Solution:** Configure Postfix to listen on Docker bridge:
```bash
# Edit /etc/postfix/main.cf
inet_interfaces = 127.0.0.1, [::1], 172.17.0.1

# Restart Postfix
sudo systemctl restart postfix

# Verify
sudo netstat -tlnp | grep :25
```

**Test from container:**
```bash
docker compose exec grafana telnet 172.17.0.1 25
```

### SSL Certificate Issues
- Verify DNS: `grafana.brendanbank.com` points to server
- Check Traefik logs: `docker compose logs traefik | grep -i acme`
- Verify Let's Encrypt config in `.env`

### Plugin Issues
```bash
docker compose exec grafana grafana-cli plugins ls
docker compose logs grafana | grep -i plugin
docker compose restart grafana
```

### OnCall Plugin Not Connected
OnCall requires backend. Use Grafana Alerting instead, or configure OnCall backend (see OnCall section above).

## Management Commands

```bash
# Start
docker compose up -d grafana

# Stop
docker compose stop grafana

# Restart
docker compose restart grafana

# View logs
docker compose logs -f grafana

# Update
docker compose pull grafana
docker compose up -d grafana

# Remove (keeps data)
docker compose rm grafana

# Remove data (⚠️ destructive)
rm -rf grafana/data/*
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAFANA_ADMIN_USER` | `admin` | Admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Admin password (change this!) |
| `GRAFANA_PLUGINS` | (empty) | Comma-separated plugin IDs |
| `GRAFANA_SMTP_HOST` | `host.docker.internal` | SMTP host (port included, e.g., `172.17.0.1:25`) |
| `TRAEFIK_CERT_RESOLVER` | `myresolver` | Traefik cert resolver |

### Volume Mounts
- `./grafana/grafana.ini:/etc/grafana/grafana.ini` - Config file
- `./grafana/data:/var/lib/grafana` - Persistent data
- `./grafana/provisioning:/etc/grafana/provisioning` - Provisioning

### Network
- **Network:** `grafana-network` (isolated)
- **Port:** 3000 (internal, accessed via Traefik)

## Security Best Practices

1. Change default password immediately
2. Use strong `GRAFANA_ADMIN_PASSWORD`
3. Invite-only sign-up (already configured)
4. Regular updates: `docker compose pull grafana && docker compose up -d grafana`
5. Regular backups of `grafana/data/`
6. Monitor logs for suspicious activity
7. Network isolation (already configured)
8. HTTPS via Traefik (already configured)
9. Never commit `.env` with passwords

## Resources

- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)
- [Plugin Catalog](https://grafana.com/grafana/plugins/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
