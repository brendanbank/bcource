#!/bin/bash
# Deploy and debug Grafana proxy

set -e

echo "=== Deploying Grafana Proxy Updates ==="
cd /usr/local/bcourse/bcourse_docker

echo "1. Pulling latest changes..."
git pull

echo "2. Restarting grafana-proxy container..."
docker compose restart grafana-proxy

echo "3. Waiting for container to start..."
sleep 2

echo "4. Reloading nginx configuration..."
docker compose exec grafana-proxy nginx -s reload || echo "Note: Container might need a moment to fully start"

echo ""
echo "=== Debugging ==="
echo ""

echo "5. Testing direct Grafana connection:"
curl -I -k https://srv6.bgwlan.nl:3000 2>&1 | head -15
echo ""

echo "6. Testing proxy connection:"
curl -I https://grafana.brendanbank.com 2>&1 | head -15
echo ""

echo "7. Checking nginx access logs (last 20 lines):"
docker compose exec grafana-proxy tail -20 /var/log/nginx/grafana-access.log 2>/dev/null || echo "Log file not found yet"
echo ""

echo "8. Checking nginx error logs (last 20 lines):"
docker compose exec grafana-proxy tail -20 /var/log/nginx/grafana-error.log 2>/dev/null || echo "Log file not found yet"
echo ""

echo "9. Checking Traefik logs (grafana related):"
docker compose logs traefik 2>&1 | grep -i grafana | tail -10
echo ""

echo "10. Container status:"
docker compose ps grafana-proxy
echo ""

echo "=== Debug Complete ==="
echo ""
echo "To monitor logs in real-time:"
echo "  docker compose exec grafana-proxy tail -f /var/log/nginx/grafana-access.log"
echo "  docker compose logs -f traefik | grep grafana"

