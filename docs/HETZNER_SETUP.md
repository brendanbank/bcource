# Hetzner setup

Host: `<user>@<server-hostname>`
App path: `/usr/local/bcource/`

## 1. Apt packages

### If running with Docker (recommended)

Install Docker and supporting tools:

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  docker.io \
  docker-compose-v2
```

On Ubuntu 24.04 (Noble) the package is `docker-compose-v2`. This gives you **Compose V2**: use `docker compose` (with a space), not `docker-compose`. Check with `docker compose version`.

Optional (if you run the scheduler or one-off commands on the host):

```bash
sudo apt install -y python3.12 python3.12-venv python3-pip mysql-client
```

### If running app on host (systemd + venv, no Docker)

```bash
sudo apt update
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  python3.12 \
  python3.12-venv \
  python3-pip \
  mysql-client \
  nginx
```

- **python3.12** – app and venv
- **mysql-client** – for `wait_for_mysql.sh` (mysqladmin ping)
- **nginx** – reverse proxy in front of uWSGI (if you use it)

uWSGI is installed in the venv (`pip install -r requirements.txt` covers it if listed, or install explicitly in venv).

---

## 2. Docker

Enable and start Docker:

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Log out and back in (or `newgrp docker`) so `docker` runs without sudo.

---

## 3. Loki Docker logging driver

Containers use the `loki` log driver in `docker-compose.yml`. Install the plugin on the host. **On ARM64** (e.g. Hetzner ARM), use a tag with the `-arm64` suffix (see [Grafana Docker driver docs](https://grafana.com/docs/loki/latest/send-data/docker-driver/)).

**AMD64 (x86_64):**
```bash
docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions
```

**ARM64 (aarch64):**
```bash
docker plugin install grafana/loki-docker-driver:3.6.0-arm64 --alias loki --grant-all-permissions
```

Check:

```bash
docker plugin ls
```

You should see `loki` enabled.

**If you get:** `Error response from daemon: dial unix .../loki.sock: connect: no such file or directory`

**Why it works on amd64 but not arm64:** the old server is **amd64** (x86_64); the Hetzner server is **arm64** (aarch64). The official `grafana/loki-docker-driver:latest` is amd64-native. On arm64 the plugin fails to create the socket. So the fix is architecture-specific (see below).

The Loki plugin also often fails when Docker is installed via **Snap** (restricted environment). Use Docker from **apt** instead:

```bash
# Check if Docker is from snap
which docker && snap list 2>/dev/null | grep -i docker

# If docker is from snap: remove it and use apt Docker
sudo snap remove docker --purge
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker $USER
# Log out and back in, then:
docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions
```

If the plugin is already installed but disabled, remove and reinstall after switching to apt Docker:

```bash
docker plugin rm -f loki
docker plugin install grafana/loki-docker-driver:latest --alias loki --grant-all-permissions
```

**If the socket error persists** (even with Docker from apt): it’s usually **ARM64**. Per [Grafana's Docker driver docs](https://grafana.com/docs/loki/latest/send-data/docker-driver/), you must **add `-arm64` to the image tag** on ARM64 hosts (e.g. Hetzner ARM):

  ```bash
  docker plugin rm -f loki 2>/dev/null
  docker plugin install grafana/loki-docker-driver:3.6.0-arm64 --alias loki --grant-all-permissions
  ```

  For other versions, use `VERSION-arm64` (e.g. `3.6.7-arm64`). See [Docker Hub tags](https://hub.docker.com/r/grafana/loki-docker-driver/tags) for available `*-arm64` tags.

- **Workaround (if no arm64 tag works): run without the Loki plugin** so the stack still starts. Use the default Docker log driver (json-file) and remove or comment out the `logging:` block from each service in `docker-compose.yml`. You can ship logs to Loki later with Promtail (e.g. scraping `/var/lib/docker/containers/*/*.log` or using the journald driver). To quickly get bcourse running, comment out every `logging:` section (the block starting with `logging:` and its `driver:` / `options:` under each of `traefik`, `bcourse`, `mysql`) and run `docker compose up -d`.

### Loki URL in compose

Compose is set to push logs to:

- `https://<loki-host>:3100/loki/api/v1/push`

If your Loki on Hetzner uses another URL, set it via env or override:

1. **Env file** (e.g. `.env` in `bcourse_docker/` or project root):

   ```bash
   LOKI_URL=https://your-loki-host:3100/loki/api/v1/push
   ```

   Then in `docker-compose.yml` use `${LOKI_URL}` in each service’s `logging.options.loki-url`.

2. **Override file** (e.g. `docker-compose.override.yml`) with the same `logging` block and your `loki-url`.

Current snippet (same for each service that uses Loki):

```yaml
logging:
  driver: "loki"
  options:
    loki-url: "https://<loki-host>:3100/loki/api/v1/push"
    loki-pipeline-stages: |
      - json:
          expressions:
            stream: stream
            attrs: attrs
            tag: attrs.tag
            level: attrs.level
            msg: log
    loki-relabel-config: |
      - action: replace
        source_labels: ['__filename__']
        target_label: 'job'
      - action: replace
        source_labels: ['container_name']
        target_label: 'container'
      - action: replace
        source_labels: ['stream']
        target_label: 'stream'
```

Ensure the Loki server is reachable from the application host (firewall and TLS).

---

## 4. Quick start (Docker Compose V2)

```bash
cd /usr/local/bcource
cp bcourse_docker/env.production bcourse_docker/.env
# Edit bcourse_docker/.env: passwords, TRAEFIK_HOST1/TRAEFIK_HOST2, ACME_ACCOUNT, etc.

cd bcourse_docker
docker compose up -d    # V2: "compose" with a space
# For production Let's Encrypt, ensure .env has ACME_CASERVER and ACME_ACCOUNT set (see env.production).
```

If the app talks to MySQL in the same compose, ensure `MYSQL_HOSTNAME` (or the DB host in `SQLALCHEMY_DATABASE_URI`) matches the MySQL service name (e.g. `bcourse-mysql` / `mysql`).

---

## 5. Scheduler on host (if not in Docker)

If the scheduler runs as systemd on the host:

- Use the same venv as the app: e.g. `/usr/local/bcource/venv/bin/python run_scheduler.py`.
- Ensure the host can resolve the MySQL host (e.g. add `127.0.0.1 mysql` to `/etc/hosts` if MySQL is published on localhost).
- Point `ExecStart` at the venv Python in `bcourse-scheduler.service`.

---

## 6. Summary checklist

| Item | Command / note |
|------|----------------|
| Apt (Docker + Compose V2) | `apt install docker.io docker-compose-v2 git curl ca-certificates` (Ubuntu Noble: `docker-compose-v2`) — then use `docker compose` |
| Apt (host app) | `apt install python3.12 python3.12-venv python3-pip mysql-client nginx` |
| Loki plugin | AMD64: `.../loki-docker-driver:latest` — ARM64: `.../loki-docker-driver:3.6.0-arm64` (see [Grafana docs](https://grafana.com/docs/loki/latest/send-data/docker-driver/)) |
| Loki URL | Adjust in compose or `.env` to match your Loki host |
| User in docker group | `usermod -aG docker $USER` then re-login |
