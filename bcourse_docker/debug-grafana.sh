#!/bin/bash
# Debug script for Grafana redirect issues

echo "=== Testing Grafana Proxy ==="
echo ""

echo "1. Testing direct connection to Grafana (srv6):"
curl -I -k https://srv6.bgwlan.nl:3000 2>&1 | head -20
echo ""

echo "2. Testing proxy connection (grafana.brendanbank.com):"
curl -I https://grafana.brendanbank.com 2>&1 | head -20
echo ""

echo "3. Checking nginx access logs:"
docker compose exec grafana-proxy tail -20 /var/log/nginx/grafana-access.log 2>/dev/null || echo "Log file not found or container not running"
echo ""

echo "4. Checking nginx error logs:"
docker compose exec grafana-proxy tail -20 /var/log/nginx/grafana-error.log 2>/dev/null || echo "Log file not found or container not running"
echo ""

echo "5. Checking Traefik logs:"
docker compose logs traefik 2>&1 | grep -i grafana | tail -10
echo ""

echo "6. Testing with verbose curl (shows redirect chain):"
curl -v -L https://grafana.brendanbank.com 2>&1 | grep -E "(Location:|HTTP/|Host:)" | head -20
echo ""

echo "=== Debug Complete ==="

