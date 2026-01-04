# Grafana Configuration Guide

This guide explains how to configure and deploy Grafana using Docker Compose in the bcourse infrastructure.

## Overview

Grafana is deployed as a separate service with **network isolation** for security. It runs on its own Docker network (`grafana-network`) and **cannot access the database** or other application services. Access is provided through Traefik reverse proxy with automatic SSL certificate management via Let's Encrypt.

## Prerequisites

- Docker and Docker Compose installed
- Traefik reverse proxy configured and running
- DNS configured for `grafana.brendanbank.com` (or your configured domain)
- Ports 80 and 443 accessible for Let's Encrypt validation (production)

## Directory Structure

Create the following directory structure in `bcourse_docker/`:

```
bcourse_docker/
├── grafana/
│   ├── grafana.ini          # Grafana configuration file
│   └── data/                 # Grafana data directory (persistent storage)
└── docker-compose.yml        # Already configured
```

### Create Directories

```bash
cd bcourse_docker
mkdir -p grafana/data
chmod 777 grafana/data  # Grafana needs write access
```

## Configuration Files

### 1. Grafana Configuration File (`grafana/grafana.ini`)

The `grafana.ini` file is already included in the repository. It contains:

- **Server settings**: Domain, root URL, port configuration
- **Database**: SQLite by default (can be changed to MySQL/PostgreSQL)
- **SMTP**: Configured to use `host.docker.internal:25` for email notifications
- **Security**: Authentication and security headers
- **Logging**: Console and file logging configuration

**Key Configuration Sections:**

```ini
[server]
domain = grafana.brendanbank.com
root_url = https://grafana.brendanbank.com/
http_port = 3000

[database]
type = sqlite3
path = grafana.db

[smtp]
enabled = true
host = host.docker.internal:25
from_address = admin@grafana.brendanbank.com
```

**Note:** For production, consider using an external database (MySQL/PostgreSQL) instead of SQLite. You can configure this in the `[database]` section of `grafana.ini`.

### 2. Environment Variables

Add Grafana configuration to your `.env` file (in the project root):

```bash
# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_grafana_password_here
GRAFANA_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource

# Optional: Traefik Certificate Resolver (defaults to myresolver)
TRAEFIK_CERT_RESOLVER=myresolver
```

**Important:** Change `GRAFANA_ADMIN_PASSWORD` to a secure password before deploying!

## Network Isolation

Grafana runs on a separate Docker network (`grafana-network`) for security:

- ✅ **Can access:** Traefik (for routing), host machine via `host.docker.internal`
- ❌ **Cannot access:** MySQL database, bcourse application, or any services on `web-network`

This isolation ensures that even if Grafana is compromised, it cannot access your application database.

### Network Architecture

```
┌─────────────────┐
│     Traefik     │ ← On both networks (routes traffic)
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────────┐
│ web-  │ │ grafana-    │
│network│ │ network     │
└───┬───┘ └──┬──────────┘
    │        │
┌───▼───┐ ┌──▼──────┐
│MySQL  │ │ Grafana │
│bcourse│ │         │
└───────┘ └─────────┘
```

## Starting Grafana

### Start All Services

```bash
cd bcourse_docker
docker compose up -d
```

### Start Only Grafana

```bash
cd bcourse_docker
docker compose up -d grafana
```

### View Logs

```bash
docker compose logs -f grafana
```

## Accessing Grafana

### Production Access

Once Traefik obtains the SSL certificate (may take a few minutes), access Grafana at:

- **Primary:** https://grafana.brendanbank.com
- **Alternative:** https://bcourse-app.bgwlan.nl (if configured)

### Local Development Access

For local development, Grafana is also accessible via:

- http://localhost (when accessing through Traefik)
- http://127.0.0.1 (when accessing through Traefik)

**Note:** Grafana is configured to only accept HTTPS connections in production. For local development, you may need to adjust Traefik configuration or use the development override file.

## Default Credentials

- **Username:** `admin` (or value from `GRAFANA_ADMIN_USER`)
- **Password:** Value from `GRAFANA_ADMIN_PASSWORD` environment variable

**⚠️ Security:** Change the default password immediately after first login!

## Plugins

Grafana supports a wide variety of plugins for panels, data sources, and apps. This section covers how to install and configure plugins.

### Installing Plugins

#### Method 1: Environment Variable (Recommended)

Add plugins to the `GRAFANA_PLUGINS` environment variable in your `.env` file (comma-separated):

```bash
GRAFANA_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource,grafana-piechart-panel
```

Plugins will be automatically installed when the container starts or restarts.

**Example `.env` configuration:**
```bash
# Install multiple plugins
GRAFANA_PLUGINS=grafana-clock-panel,grafana-piechart-panel,grafana-worldmap-panel,grafana-simple-json-datasource
```

#### Method 2: Manual Installation

You can also install plugins manually after the container is running:

```bash
# Install a plugin
docker compose exec grafana grafana-cli plugins install <plugin-id>

# Example: Install clock panel
docker compose exec grafana grafana-cli plugins install grafana-clock-panel

# Restart Grafana to load the plugin
docker compose restart grafana
```

#### Method 3: Via Grafana UI

1. Log into Grafana at https://grafana.brendanbank.com
2. Go to **Configuration** → **Plugins and data** → **Plugins**
3. Browse available plugins
4. Click **Install** on the desired plugin
5. Restart Grafana if required

### Popular Plugins

#### Panel Plugins

- **grafana-clock-panel** - Clock panel for dashboards
- **grafana-piechart-panel** - Pie chart visualization
- **grafana-worldmap-panel** - World map visualization
- **grafana-polystat-panel** - Multi-metric status panel
- **grafana-statusmap-panel** - Status map visualization
- **grafana-gauge-panel** - Gauge panel

#### Data Source Plugins

- **grafana-simple-json-datasource** - Simple JSON data source
- **grafana-influxdb-datasource** - InfluxDB data source
- **grafana-elasticsearch-datasource** - Elasticsearch data source
- **grafana-cloudwatch-datasource** - AWS CloudWatch data source
- **grafana-prometheus-datasource** - Prometheus data source

#### App Plugins

- **grafana-kubernetes-app** - Kubernetes monitoring
- **grafana-zabbix-app** - Zabbix integration

### Plugin Configuration

#### Configuring Plugins via Environment Variables

Some plugins can be configured via environment variables. Add these to your `.env` file:

```bash
# Example: Configure a plugin
GF_PLUGINS_<PLUGIN_ID>_<SETTING>=value
```

#### Configuring Plugins via grafana.ini

Add plugin-specific configuration to `grafana/grafana.ini`:

```ini
[plugins]
# Allow loading unsigned plugins (use with caution)
allow_loading_unsigned_plugins = plugin-id-1,plugin-id-2

# Enable plugin scanner
plugin_admin_enabled = true

# Plugin catalog URL
plugin_catalog_url = https://grafana.com/grafana/plugins/
```

#### Configuring Plugins via UI

1. Log into Grafana
2. Go to **Configuration** → **Plugins and data** → **Plugins**
3. Select your installed plugin
4. Click **Configure** to set plugin-specific settings

### Plugin Management Commands

```bash
# List installed plugins
docker compose exec grafana grafana-cli plugins ls

# List available plugins
docker compose exec grafana grafana-cli plugins list-remote

# Update all plugins
docker compose exec grafana grafana-cli plugins update-all

# Update a specific plugin
docker compose exec grafana grafana-cli plugins update <plugin-id>

# Remove a plugin
docker compose exec grafana grafana-cli plugins remove <plugin-id>

# Show plugin information
docker compose exec grafana grafana-cli plugins ls <plugin-id>
```

### Plugin Configuration Examples

#### Example 1: Clock Panel Configuration

After installing `grafana-clock-panel`, configure it in a dashboard:

1. Add a new panel
2. Select **Clock** as the visualization
3. Configure settings:
   - Time format (12/24 hour)
   - Timezone
   - Font size and color
   - Background color

#### Example 2: Simple JSON Data Source

1. Install the plugin:
   ```bash
   GRAFANA_PLUGINS=grafana-simple-json-datasource
   ```

2. Add data source in Grafana UI:
   - Go to **Configuration** → **Data sources**
   - Click **Add data source**
   - Select **Simple JSON**
   - Configure URL and authentication

3. Use in dashboards:
   - Create a new dashboard
   - Add panel
   - Select Simple JSON data source
   - Configure queries

#### Example 3: Pie Chart Panel

1. Install:
   ```bash
   GRAFANA_PLUGINS=grafana-piechart-panel
   ```

2. Use in dashboard:
   - Add panel → Select **Pie Chart**
   - Configure data source
   - Set labels and values
   - Customize colors and legend

### Plugin Troubleshooting

#### Plugin Not Appearing

1. **Check installation:**
   ```bash
   docker compose exec grafana grafana-cli plugins ls
   ```

2. **Check logs:**
   ```bash
   docker compose logs grafana | grep -i plugin
   ```

3. **Restart Grafana:**
   ```bash
   docker compose restart grafana
   ```

#### Plugin Loading Errors

1. **Check plugin compatibility:**
   - Verify plugin is compatible with your Grafana version
   - Check plugin documentation

2. **Check permissions:**
   ```bash
   docker compose exec grafana ls -la /var/lib/grafana/plugins
   ```

3. **Check plugin signature:**
   - Some plugins require signature verification
   - Add to `allow_loading_unsigned_plugins` if needed

#### Plugin Configuration Not Saving

1. **Check data directory permissions:**
   ```bash
   ls -la grafana/data/
   ```

2. **Verify volume mount:**
   ```bash
   docker compose exec grafana ls -la /var/lib/grafana
   ```

3. **Check Grafana logs:**
   ```bash
   docker compose logs grafana
   ```

### Plugin Best Practices

1. **Use Official Plugins:** Prefer plugins from the official Grafana plugin catalog
2. **Version Compatibility:** Ensure plugins are compatible with your Grafana version
3. **Security:** Review plugin permissions and only install trusted plugins
4. **Backup:** Backup plugin configurations along with dashboards
5. **Documentation:** Document which plugins are installed and why
6. **Updates:** Regularly update plugins for bug fixes and security patches

### Plugin Installation Workflow

1. **Add to `.env`:**
   ```bash
   GRAFANA_PLUGINS=plugin-id-1,plugin-id-2
   ```

2. **Restart Grafana:**
   ```bash
   docker compose restart grafana
   ```

3. **Verify installation:**
   ```bash
   docker compose exec grafana grafana-cli plugins ls
   ```

4. **Configure in UI:**
   - Log into Grafana
   - Configure plugin settings
   - Use in dashboards

### Finding Plugins

- **Official Catalog:** https://grafana.com/grafana/plugins/
- **Search:** Use the Grafana UI plugin browser
- **Documentation:** Check plugin-specific documentation for configuration details

## Data Persistence

Grafana data is stored in `./grafana/data/` directory, which is mounted as a volume. This includes:

- Dashboards
- Data sources
- Users and organizations
- Plugin data
- SQLite database (if using default configuration)

**Backup:** Regularly backup the `grafana/data` directory to prevent data loss.

```bash
# Backup Grafana data
tar -czf grafana-backup-$(date +%Y%m%d).tar.gz grafana/data/

# Restore Grafana data
tar -xzf grafana-backup-YYYYMMDD.tar.gz
```

## Troubleshooting

### Grafana Container Won't Start

1. **Check logs:**
   ```bash
   docker compose logs grafana
   ```

2. **Verify directory permissions:**
   ```bash
   ls -la grafana/data
   # Should show write permissions for Grafana user (UID 472)
   ```

3. **Check configuration file:**
   ```bash
   docker compose exec grafana cat /etc/grafana/grafana.ini
   ```

### Traefik Can't Route to Grafana

1. **Verify Grafana is running:**
   ```bash
   docker compose ps grafana
   ```

2. **Check Traefik logs:**
   ```bash
   docker compose logs traefik | grep grafana
   ```

3. **Verify network connectivity:**
   ```bash
   docker compose exec traefik ping grafana
   ```

4. **Check Traefik dashboard:**
   - Access http://localhost:8080 (Traefik dashboard)
   - Look for Grafana service in the HTTP services list

### SSL Certificate Issues

If SSL certificate generation fails:

1. **Check DNS:** Ensure `grafana.brendanbank.com` points to your server
2. **Check Traefik logs:**
   ```bash
   docker compose logs traefik | grep -i acme
   ```
3. **Verify Let's Encrypt configuration** in `.env`:
   ```bash
   ACME_CASERVER=https://acme-v02.api.letsencrypt.org/directory
   ACME_ACCOUNT=your-email@example.com
   ```

### Cannot Access Host Machine

Grafana is configured with `host.docker.internal:host-gateway` to access the host machine. This allows:

- Connecting to databases running on the host
- Accessing services on the host network
- Using host-based data sources (like SMTP on port 25)

If this doesn't work, verify Docker version (requires Docker 20.10+) or configure manually.

### Database Connection Issues

If you're trying to connect Grafana to an external database:

1. **For MySQL/PostgreSQL on host:** Use `host.docker.internal` as the hostname
2. **For MySQL/PostgreSQL in Docker:** Ensure the database is accessible from the `grafana-network` or use `host.docker.internal` with port mapping
3. **Check firewall:** Ensure ports are accessible

**Note:** Grafana cannot directly connect to MySQL in the `web-network` due to network isolation. Use `host.docker.internal` if MySQL is exposed on the host.

## Security Best Practices

1. **Change Default Password:** Always change the admin password after first login
2. **Use Strong Passwords:** Set a strong `GRAFANA_ADMIN_PASSWORD` in `.env`
3. **Disable Sign-up:** Already configured (`allow_sign_up = false` in grafana.ini)
4. **Limit Access:** Use firewall rules to restrict access to Grafana
5. **Regular Updates:** Keep Grafana image updated:
   ```bash
   docker compose pull grafana
   docker compose up -d grafana
   ```
6. **Backup Data:** Regularly backup `grafana/data` directory
7. **Monitor Logs:** Regularly check Grafana logs for suspicious activity
8. **Network Isolation:** Keep Grafana on separate network (already configured)
9. **SSL/TLS:** Always use HTTPS in production (configured via Traefik)
10. **Environment Variables:** Never commit `.env` file with passwords to version control

## Updating Grafana

To update Grafana to the latest version:

```bash
cd bcourse_docker
docker compose pull grafana
docker compose up -d grafana
```

**Note:** Before updating, backup your Grafana data directory.

## Stopping Grafana

### Stop Grafana Service

```bash
docker compose stop grafana
```

### Remove Grafana Container (keeps data)

```bash
docker compose rm grafana
```

### Remove Grafana and Data (⚠️ Destructive)

```bash
docker compose down grafana
rm -rf grafana/data/*
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password (change this!) |
| `GRAFANA_PLUGINS` | (empty) | Comma-separated list of plugins to install |
| `TRAEFIK_CERT_RESOLVER` | `myresolver` | Traefik certificate resolver name |

### Volume Mounts

- `./grafana/grafana.ini:/etc/grafana/grafana.ini` - Configuration file
- `./grafana/data:/var/lib/grafana` - Persistent data storage

### Network

- **Network:** `grafana-network` (isolated from database)
- **Port:** 3000 (internal, accessed via Traefik)

## Additional Resources

- [Grafana Official Documentation](https://grafana.com/docs/grafana/latest/)
- [Grafana Configuration Reference](https://grafana.com/docs/grafana/latest/setup-grafana/configure-grafana/)
- [Grafana Docker Image](https://hub.docker.com/r/grafana/grafana)
- [Traefik Documentation](https://doc.traefik.io/traefik/)

## Support

For issues specific to this deployment:

1. Check container logs: `docker compose logs grafana`
2. Verify configuration: `docker compose config`
3. Check Traefik routing: `docker compose logs traefik | grep grafana`
4. Verify network isolation: `docker network inspect grafana-network`

