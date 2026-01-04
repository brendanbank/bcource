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

# SMTP Configuration (if host.docker.internal doesn't work)
# Find your Docker bridge gateway IP: docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'
GRAFANA_SMTP_HOST=host.docker.internal  # or 172.17.0.1 or your SMTP server IP
GRAFANA_SMTP_PORT=25

# Google OAuth Configuration (for @google.com users)
# Get credentials from: https://console.cloud.google.com/apis/credentials
# See "Authentication" section below for setup instructions
GRAFANA_GOOGLE_CLIENT_ID=your_google_client_id_here
GRAFANA_GOOGLE_CLIENT_SECRET=your_google_client_secret_here

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

## Authentication

Grafana supports multiple authentication methods:

### Default Login

- **Username:** `admin` (or value from `GRAFANA_ADMIN_USER`)
- **Password:** Value from `GRAFANA_ADMIN_PASSWORD` environment variable

**⚠️ Security:** Change the default password immediately after first login!

### Google OAuth (for any Google account)

Google OAuth is configured to allow **any Google account** to sign in, including:
- Gmail accounts (@gmail.com)
- Google Workspace accounts (@google.com)
- Custom domain Google Workspace accounts (e.g., @brendanbank.com, @example.com)

#### Setup Instructions

1. **Create Google OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Navigate to **APIs & Services** → **Credentials**
   - Click **+ Create Credentials** → **OAuth client ID**
   - Choose **Web application**
   - Configure:
     - **Name:** Grafana (or your preferred name)
     - **Authorized JavaScript origins:** `https://grafana.brendanbank.com`
     - **Authorized redirect URIs:** `https://grafana.brendanbank.com/login/google`
   - Click **Create**
   - Copy the **Client ID** and **Client Secret**

2. **Add Credentials to `.env` File:**
   ```bash
   GRAFANA_GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GRAFANA_GOOGLE_CLIENT_SECRET=your_client_secret_here
   ```

3. **Restart Grafana:**
   ```bash
   cd bcourse_docker
   docker compose restart grafana
   ```

4. **Test Login:**
   - Go to https://grafana.brendanbank.com
   - Click **Sign in with Google**
   - Any Google account (Gmail, Google Workspace, custom domains) can now sign in

#### Domain Restrictions (Optional)

By default, **all Google accounts** are allowed. To restrict access to specific domains:

1. **Add to `.env` file:**
   ```bash
   # Allow only specific domains (comma-separated)
   GRAFANA_GOOGLE_ALLOWED_DOMAINS=gmail.com,google.com,brendanbank.com
   
   # Or leave empty/unset to allow all Google accounts
   # GRAFANA_GOOGLE_ALLOWED_DOMAINS=
   ```

2. **Restart Grafana:**
   ```bash
   docker compose restart grafana
   ```

#### Security Notes

- **By default, any Google account can sign in** (Gmail, Google Workspace, custom domains)
- To restrict to specific domains, set `GRAFANA_GOOGLE_ALLOWED_DOMAINS` in `.env`
- First-time users will be automatically created in Grafana
- Users can still use the default admin login if needed
- Google OAuth credentials are stored securely in environment variables

#### Troubleshooting

**"Invalid redirect URI" error:**
- Ensure the redirect URI in Google Console matches exactly: `https://grafana.brendanbank.com/login/google`
- Check that your domain matches `grafana.brendanbank.com`

**"Access blocked" error:**
- Verify the authorized JavaScript origin is set to: `https://grafana.brendanbank.com`
- Check that OAuth consent screen is configured in Google Console

**Users can't sign in:**
- Verify `allowed_domains = google.com` in `grafana.ini`
- Check Grafana logs: `docker compose logs grafana | grep -i google`

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
- **grafana-oncall-app** - Incident Response Management (OnCall) - **Installed**

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

## Alerting and Incident Response Management (IRM)

Grafana includes built-in **Alerting** capabilities and supports **Grafana OnCall** for comprehensive incident response management.

### Grafana Alerting (Built-in) ✅ Recommended

Grafana Alerting is a built-in feature (available in Grafana 8.0+) that allows you to create and manage alert rules based on your monitoring data. **This is the recommended solution** as it requires no backend setup and provides comprehensive alerting capabilities.

#### Features

- **Alert Rules**: Create alert rules based on queries from any data source
- **Contact Points**: Configure multiple notification channels (email, Slack, webhooks, etc.)
- **Notification Policies**: Route alerts to appropriate contact points based on labels
- **Alert Groups**: Group related alerts together
- **Silences**: Temporarily silence alerts for maintenance
- **No Backend Required**: Works out of the box with your existing Grafana installation

#### Getting Started with Alerting

**Step 1: Access Alerting**
- Log into Grafana at https://grafana.brendanbank.com
- Navigate to **Alerts & IRM** → **Alerting** in the main menu

**Step 2: Create a Contact Point (Email is already configured!)**
- Go to **Alerting** → **Contact points**
- You'll see a default email contact point using your SMTP configuration
- Click **+ Add contact point** to add more channels:
  - **Pushover** - Push notifications to your phone (recommended for mobile)
  - **Telegram** - Telegram bot notifications
  - **Slack** - Slack notifications (can forward to mobile)
  - **PagerDuty** - Incident management with mobile app
  - **OpsGenie** - Alerting with mobile app
  - **Webhook** - Custom integrations
- Test the contact point to verify it works

**Step 3: Create an Alert Rule**
- Go to **Alerting** → **Alert rules**
- Click **+ New alert rule**
- **Define the query:**
  - Select your data source (Prometheus, MySQL, etc.)
  - Write a query that returns metrics you want to monitor
- **Set conditions:**
  - Define when the alert should fire (e.g., value > threshold)
  - Set evaluation interval (how often to check)
  - Set "for" duration (how long condition must be true before alerting)
- **Configure notifications:**
  - Assign contact points
  - Add labels for routing
  - Set alert summary and description

**Step 4: Configure Notification Policies (Optional)**
- Go to **Alerting** → **Notification policies**
- Set up routing rules based on labels
- Configure group-by settings and timing
- Define when to send notifications (immediately, after delay, etc.)

#### Quick Example: Create Your First Alert

1. **Go to Alerting → Alert rules → + New alert rule**

2. **Set up the query:**
   ```
   Data source: Your data source (e.g., Prometheus, MySQL)
   Query: SELECT avg(cpu_usage) FROM metrics WHERE time > now() - 5m
   ```

3. **Set conditions:**
   ```
   Condition: When avg(cpu_usage) > 80
   Evaluate every: 1m
   For: 5m (alert only if condition persists for 5 minutes)
   ```

4. **Configure notifications:**
   ```
   Contact point: Email (default)
   Summary: High CPU usage detected
   Description: CPU usage is {{ $values.A.Value }}%, exceeding threshold of 80%
   ```

5. **Add labels (optional):**
   ```
   severity: warning
   team: infrastructure
   ```

6. **Save and test** - The alert will start evaluating immediately!

#### Alerting Configuration

Alerting is configured via `grafana.ini`:

```ini
[unified_alerting]
# Enable unified alerting (default: true in Grafana 9.0+)
enabled = true

# Alert evaluation interval
evaluation_timeout_seconds = 30

# Default contact point
default_contact_point = email
```

#### SMTP Configuration for Email Alerts

Email notifications use the SMTP configuration already set up in `grafana.ini`:

```ini
[smtp]
enabled = true
host = 172.17.0.1:25
from_address = admin@grafana.brendanbank.com
```

See the [SMTP Configuration](#smtp-connection-issues) section for troubleshooting.

#### Mobile Push Notifications

Grafana Alerting supports several ways to get push notifications on your phone:

**Option 1: Pushover (Recommended - Easiest)**
1. Sign up for Pushover at https://pushover.net (free trial, then $5 one-time per platform)
2. Install Pushover app on your phone (iOS/Android)
3. Get your User Key from Pushover dashboard
4. Create a new Application in Pushover to get an API Token
5. In Grafana: **Alerting** → **Contact points** → **+ Add contact point**
   - Type: **Pushover**
   - User key: Your Pushover user key
   - API token: Your Pushover application token
   - Priority: High (for important alerts)
6. Add this contact point to your alert rules

**Option 2: Telegram**
1. Create a Telegram bot via @BotFather
2. Get your chat ID (send message to bot, then visit `https://api.telegram.org/bot<token>/getUpdates`)
3. In Grafana: **Alerting** → **Contact points** → **+ Add contact point**
   - Type: **Telegram**
   - Bot token: Your Telegram bot token
   - Chat ID: Your Telegram chat ID

**Option 3: Slack (with mobile app)**
1. Create a Slack webhook URL
2. In Grafana: **Alerting** → **Contact points** → **+ Add contact point**
   - Type: **Slack**
   - Webhook URL: Your Slack webhook URL
3. Install Slack mobile app to receive push notifications

**Option 4: PagerDuty or OpsGenie**
- Professional incident management platforms with mobile apps
- More features but requires account setup
- Good for teams and on-call rotations

**Quick Setup Example - Pushover:**
```bash
# 1. Sign up at pushover.net and install app
# 2. Get User Key and create Application for API Token
# 3. In Grafana UI:
#    - Alerting → Contact points → + Add contact point
#    - Select "Pushover"
#    - Enter User Key and API Token
#    - Set Priority: High
#    - Save and test
# 4. Add this contact point to your alert rules
```

#### Do You Need Prometheus Alertmanager?

**No, you don't need an external Alertmanager for Grafana Alerting.**

Grafana Alerting is **self-contained** and handles everything:
- Alert rule evaluation
- Alert routing and grouping
- Notification delivery
- Alert state management

**When you might use Alertmanager:**
- If you're using Prometheus and want Prometheus-native alerting
- If you want to route Prometheus alerts through Alertmanager first
- If you have existing Alertmanager configurations you want to keep

**Grafana Alerting can integrate with Alertmanager:**
- You can configure Grafana Alerting to send alerts to Prometheus Alertmanager
- Or use Alertmanager as a contact point in Grafana Alerting
- This is optional - Grafana Alerting works perfectly fine standalone

**For your setup:** Since you're using Grafana Alerting, you don't need Alertmanager unless you have specific requirements to integrate with Prometheus Alertmanager.

#### Alerting Resources

- [Grafana Alerting Documentation](https://grafana.com/docs/grafana/latest/alerting/)
- [Get Started with Alerting Tutorial](https://grafana.com/tutorials/alerting-get-started/)
- [Alert Rule Best Practices](https://grafana.com/docs/grafana/latest/alerting/fundamentals/alert-rules/)
- [Integrating with Prometheus Alertmanager](https://grafana.com/docs/grafana/latest/alerting/set-up/migrating-alerts/)

### Grafana OnCall (Plugin)

Grafana OnCall is an incident response management plugin that provides on-call scheduling, alert routing, and incident management workflows.

#### ⚠️ Important: OnCall Requires a Backend Service

**Grafana OnCall requires a separate backend service to function.** The plugin alone is not sufficient. You have two options:

1. **Grafana Cloud OnCall** (Easiest) - Use Grafana Cloud's managed OnCall service
2. **Self-Hosted OnCall Backend** (Complex) - Set up your own OnCall backend with PostgreSQL, Redis, etc.

#### Features

- **On-Call Schedules**: Create rotating on-call schedules
- **Escalation Chains**: Define multi-level escalation policies
- **Alert Routing**: Route alerts to the right on-call person
- **Incident Management**: Track and manage incidents
- **Integration**: Integrate with Grafana Alerting and other alert sources

#### Installation

Grafana OnCall plugin is already installed via the `grafana-oncall-app` plugin. It's configured in your `.env`:

```bash
GRAFANA_PLUGINS=grafana-clock-panel,grafana-piechart-panel,grafana-oncall-app
```

However, **the plugin requires backend configuration** before it can be used.

#### Option 1: Using Grafana Cloud OnCall (Recommended for Most Users)

If you have a Grafana Cloud account:

1. **Get Your OnCall URL and Stack ID:**
   - Log into Grafana Cloud
   - Navigate to your OnCall instance
   - Get your OnCall API URL and Stack ID from the settings

2. **Update Provisioning Configuration:**
   - Edit `grafana/provisioning/plugins/oncall.yaml`
   - Set `onCallApiUrl` to your Grafana Cloud OnCall URL
   - Set `stackId` to your Cloud stack ID

3. **Restart Grafana:**
   ```bash
   docker compose restart grafana
   ```

#### Option 2: Self-Hosted OnCall Backend

Setting up a self-hosted OnCall backend requires:
- PostgreSQL database
- Redis cache
- OnCall engine service
- Additional configuration

This is complex and typically requires multiple Docker containers. See the [OnCall Self-Hosted Documentation](https://grafana.com/docs/oncall/latest/open-source/) for full setup instructions.

#### Option 3: Use Grafana Alerting Instead ✅ Recommended

**Grafana Alerting** (built-in) is recommended and provides sufficient functionality for most use cases:
- Alert rules and notifications
- Contact points (email, Slack, webhooks)
- Notification policies
- Alert grouping
- No backend services required

See the [Alerting section](#grafana-alerting-built-in) above for setup instructions.

**Note:** If you're using Grafana Alerting, you can optionally remove the OnCall plugin from your `.env` file to avoid confusion:
```bash
# Remove grafana-oncall-app from GRAFANA_PLUGINS in .env
GRAFANA_PLUGINS=grafana-clock-panel,grafana-piechart-panel
```

#### Getting Started with OnCall (After Backend is Configured)

1. **Access OnCall:**
   - Log into Grafana at https://grafana.brendanbank.com
   - Navigate to **Apps** → **OnCall** in the main menu
   - Or go to **Alerts & IRM** → **OnCall**

2. **Initial Setup:**
   - Create an on-call schedule
   - Add team members and their contact information
   - Set up escalation chains
   - Configure integrations with alert sources

3. **Create Integrations:**
   - Go to **Integrations** in OnCall
   - Add integrations for Grafana Alerting, Prometheus, etc.
   - Configure alert templates and routing rules

4. **Set Up Schedules:**
   - Go to **Schedules**
   - Create on-call rotations
   - Assign team members to rotations
   - Configure time zones and shift patterns

5. **Configure Escalation Chains:**
   - Go to **Escalation chains**
   - Define escalation steps
   - Set timeouts and notification methods

#### OnCall Configuration

OnCall is configured via provisioning file at `grafana/provisioning/plugins/oncall.yaml`:

```yaml
apiVersion: 1

apps:
  - type: grafana-oncall-app
    org_id: 1
    enabled: true
    jsonData:
      stackId: 1          # Your OnCall stack ID (from Cloud or self-hosted)
      orgId: 1            # Your Grafana organization ID
      onCallApiUrl: http://oncall-engine:8080  # Your OnCall backend URL
```

**Current Configuration:**
- The provisioning file is set up at `grafana/provisioning/plugins/oncall.yaml`
- It's mounted into Grafana at `/etc/grafana/provisioning`
- Update the `stackId` and `onCallApiUrl` based on your OnCall backend setup

For advanced configuration, see the [OnCall Documentation](https://grafana.com/docs/oncall/latest/).

#### OnCall Resources

- [Grafana OnCall Documentation](https://grafana.com/docs/oncall/latest/)
- [OnCall Setup Guide](https://grafana.com/docs/oncall/latest/get-started/)
- [OnCall Integrations](https://grafana.com/docs/oncall/latest/integrations/)

### Integrating Alerting with OnCall

To integrate Grafana Alerting with OnCall:

1. **In Grafana Alerting:**
   - Create a contact point of type **OnCall**
   - Configure it to point to your OnCall instance

2. **In OnCall:**
   - Go to **Integrations** → **Grafana Alerting**
   - Add a new integration
   - Configure alert templates and routing

3. **Set Up Routing:**
   - Configure notification policies in Alerting to route to OnCall
   - Set up escalation chains in OnCall for different alert severities

### Best Practices

1. **Alert Rules:**
   - Use meaningful alert names and descriptions
   - Add labels for better routing and grouping
   - Set appropriate evaluation intervals
   - Use "for" duration to reduce false positives

2. **OnCall:**
   - Create clear escalation chains
   - Set up multiple notification methods per person
   - Regularly review and update schedules
   - Test alert routing regularly

3. **Integration:**
   - Use consistent labeling between Alerting and OnCall
   - Document alert routing policies
   - Regularly review incident response times

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

### SMTP Connection Issues

If you see errors like `dial tcp 172.17.0.1:25: connect: connection refused`:

**Problem:** `host.docker.internal` resolves to the Docker bridge gateway IP (`172.17.0.1`), but your SMTP server is likely only listening on `127.0.0.1` (localhost).

**Solution 1: Configure SMTP Server to Listen on Docker Bridge**

Make your SMTP server listen on the Docker bridge interface:

```bash
# For Postfix (common SMTP server)
# Edit /etc/postfix/main.cf
inet_interfaces = all  # or inet_interfaces = 127.0.0.1, 172.17.0.1

# Restart Postfix
sudo systemctl restart postfix
```

**Solution 2: Use Docker Bridge Gateway IP**

Find the Docker bridge gateway IP and use it directly:

```bash
# Find the gateway IP
ip addr show docker0 | grep inet

# Or check the network gateway
docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'
```

Then set in your `.env` file:
```bash
GRAFANA_SMTP_HOST=172.17.0.1  # Replace with actual gateway IP
```

**Solution 3: Use Host's Public IP**

If your SMTP server is accessible via the host's public IP:

```bash
# Find host IP
hostname -I | awk '{print $1}'

# Set in .env
GRAFANA_SMTP_HOST=<host-ip>
```

**Solution 4: Use Host Network Mode (Not Recommended)**

As a last resort, you can use host network mode, but this reduces security isolation:

```yaml
# In docker-compose.yml (not recommended)
grafana:
  network_mode: "host"
```

**Verify SMTP Server is Running:**

```bash
# Check if SMTP server is listening
sudo netstat -tlnp | grep :25
# or
sudo ss -tlnp | grep :25

# Test SMTP connection from host
telnet localhost 25
```

**Test SMTP from Grafana Container:**

```bash
# Test connection from Grafana container
docker compose exec grafana telnet host.docker.internal 25

# Or test with the gateway IP
docker compose exec grafana telnet 172.17.0.1 25
```

**Update Configuration:**

After determining the correct SMTP host, update your `.env` file:

```bash
# Add to .env
GRAFANA_SMTP_HOST=172.17.0.1  # or your SMTP server IP
GRAFANA_SMTP_PORT=25
```

Then restart Grafana:
```bash
docker compose restart grafana
```

### Database Connection Issues

If you're trying to connect Grafana to an external database:

1. **For MySQL/PostgreSQL on host:** Use `host.docker.internal` as the hostname
2. **For MySQL/PostgreSQL in Docker:** Ensure the database is accessible from the `grafana-network` or use `host.docker.internal` with port mapping
3. **Check firewall:** Ensure ports are accessible

**Note:** Grafana cannot directly connect to MySQL in the `web-network` due to network isolation. Use `host.docker.internal` if MySQL is exposed on the host.

### OnCall Plugin Connection Issues

If you see errors like "Plugin is not connected" or "jsonData.stackId is not set":

**Problem:** OnCall plugin requires a backend service to be configured and running.

**Solution Options:**

1. **Use Grafana Cloud OnCall:**
   - Sign up for Grafana Cloud (if not already)
   - Get your OnCall URL and Stack ID from Cloud settings
   - Update `grafana/provisioning/plugins/oncall.yaml` with your Cloud credentials
   - Restart Grafana

2. **Set Up Self-Hosted OnCall Backend:**
   - Requires PostgreSQL, Redis, and OnCall engine services
   - See [OnCall Self-Hosted Documentation](https://grafana.com/docs/oncall/latest/open-source/)
   - Update `onCallApiUrl` in provisioning file to point to your backend

3. **Use Grafana Alerting Instead:**
   - Grafana Alerting is built-in and doesn't require a backend
   - Provides alert rules, contact points, and notification policies
   - Sufficient for most use cases without complex on-call scheduling

**Check Provisioning Configuration:**
```bash
# Verify provisioning file exists
cat grafana/provisioning/plugins/oncall.yaml

# Check if provisioning directory is mounted
docker compose exec grafana ls -la /etc/grafana/provisioning/plugins/

# Restart Grafana after configuration changes
docker compose restart grafana
```

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
| `GRAFANA_SMTP_HOST` | `host.docker.internal` | SMTP server hostname (use Docker bridge gateway IP if host.docker.internal doesn't work) |
| `GRAFANA_SMTP_PORT` | `25` | SMTP server port |
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

