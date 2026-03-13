#!/bin/bash
# Rebuild Puppeteer service with browser installation

echo "🔨 Rebuilding Puppeteer service with Chromium browser..."
echo ""

# Stop and remove existing container
echo "🛑 Stopping Puppeteer service..."
sudo docker compose stop puppeteer-service
sudo docker compose rm -f puppeteer-service

# Rebuild (this will install Chromium)
echo ""
echo "🔨 Building Puppeteer service (this may take a few minutes)..."
sudo docker compose build --no-cache puppeteer-service

# Start service
echo ""
echo "🚀 Starting Puppeteer service..."
sudo docker compose up -d puppeteer-service

# Wait for service
echo ""
echo "⏳ Waiting for service to be ready..."
sleep 5

# Check status
echo ""
echo "📋 Service status:"
sudo docker compose ps puppeteer-service

# Check logs
echo ""
echo "📜 Recent logs:"
sudo docker compose logs --tail=30 puppeteer-service

echo ""
echo "✅ Rebuild complete!"
echo ""
echo "Test with:"
echo "  curl -X POST http://localhost:3000/start/stake -H 'Content-Type: application/json' -d '{\"headless\":true,\"url\":\"https://stake.com\"}' | python3 -m json.tool"
