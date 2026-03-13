#!/bin/bash
# Rebuild and restart Puppeteer service

echo "🔨 Rebuilding Puppeteer service..."
sudo docker compose build puppeteer-service

echo ""
echo "🛑 Stopping Puppeteer service..."
sudo docker compose stop puppeteer-service

echo ""
echo "🗑️  Removing old container..."
sudo docker compose rm -f puppeteer-service

echo ""
echo "🚀 Starting Puppeteer service..."
sudo docker compose up -d puppeteer-service

echo ""
echo "⏳ Waiting for service to be ready..."
sleep 5

echo ""
echo "📋 Service status:"
sudo docker compose ps puppeteer-service

echo ""
echo "📜 Recent logs:"
sudo docker compose logs --tail=20 puppeteer-service

echo ""
echo "✅ Done! Test health endpoint:"
echo "   curl http://localhost:3000/health"
