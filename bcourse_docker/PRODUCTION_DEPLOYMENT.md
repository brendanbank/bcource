# Production Deployment Guide

## Overview

The docker-compose.yml is already production-ready with the following features:

✅ **HTTP to HTTPS Redirect**: Automatically redirects port 80 to 443  
✅ **Environment Variables**: All ports and hosts are configurable  
✅ **Let's Encrypt**: Automatic SSL certificate generation  
✅ **Multiple Hosts**: Supports multiple domains  

## Production Setup

### 1. Create Production Environment File

Copy and modify `env.production`:

```bash
cp env.production .env
```

Edit `.env` with your production values:

```bash
# Production Environment Configuration
HTTP_PORT=80
HTTPS_PORT=443
TRAEFIK_DASHBOARD_PORT=8080

# MySQL Configuration
MYSQL_ROOT_PASSWORD=your_secure_root_password_here
MYSQL_DATABASE=bcourse
MYSQL_USER=bcourse
MYSQL_PASSWORD=your_secure_password_here

# Traefik Configuration for Production
TRAEFIK_HOST1=bcourse.nl
TRAEFIK_HOST2=www.bcourse.nl
TRAEFIK_ENTRYPOINT=websecure
TRAEFIK_CERTRESOLVER=myresolver
```

### 2. Use Production Docker Compose

Use the production version that uses the production Let's Encrypt server:

```bash
docker compose -f docker-compose.production.yml up -d
```

### 3. Verify Configuration

Check that the configuration is correct:

```bash
docker compose -f docker-compose.production.yml config
```

## Key Features

### Port Redirection
- **HTTP (80) → HTTPS (443)**: Automatic redirect configured
- **Standard Ports**: Uses ports 80 and 443 for production

### SSL Certificates
- **Automatic**: Let's Encrypt certificates generated automatically
- **Production Server**: Uses production Let's Encrypt server
- **Multiple Domains**: Supports both `bcourse.nl` and `www.bcourse.nl`

### Environment Variables
- **Flexible**: Easy to change hosts and ports
- **Secure**: Database passwords configurable
- **Portable**: Same configuration works on any server

## Testing

1. **HTTP Redirect**: `http://bcourse.nl` → `https://bcourse.nl`
2. **HTTPS Access**: `https://bcourse.nl` and `https://www.bcourse.nl`
3. **Dashboard**: `http://your-server:8080` (Traefik dashboard)

## Security Notes

- Change default passwords in `.env`
- Ensure firewall allows ports 80, 443, and 8080
- Keep Let's Encrypt certificates secure
- Monitor logs for any issues 