#!/bin/bash
# Check Puppeteer service status

echo "🔍 Checking Puppeteer service status..."
echo ""

# Check if containers are running
echo "📦 Docker containers:"
sudo docker compose ps puppeteer-service app 2>/dev/null || docker compose ps puppeteer-service app 2>/dev/null || echo "  Error: Could not check containers (try with sudo)"

echo ""
echo "🌐 Testing Puppeteer service health:"

# Try to connect to the service
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "  ✅ Puppeteer service is responding on http://localhost:3000"
    curl -s http://localhost:3000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:3000/health
else
    echo "  ❌ Puppeteer service is NOT responding on http://localhost:3000"
    echo ""
    echo "  Troubleshooting:"
    echo "  1. Check if service is running: sudo docker compose ps puppeteer-service"
    echo "  2. Check service logs: sudo docker compose logs puppeteer-service"
    echo "  3. Restart service: sudo docker compose restart puppeteer-service"
    echo "  4. Rebuild and start: sudo docker compose up -d --build puppeteer-service"
fi

echo ""
echo "📋 Service logs (last 10 lines):"
sudo docker compose logs --tail=10 puppeteer-service 2>/dev/null || docker compose logs --tail=10 puppeteer-service 2>/dev/null || echo "  Could not fetch logs"
