#!/bin/bash
# Check if Docker containers are running

echo "🔍 Checking Docker containers..."

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if containers exist
if ! docker ps -a --format '{{.Names}}' | grep -q "enrichment_postgres\|enrichment_app"; then
    echo "⚠️  Containers don't exist. Starting them..."
    docker compose up -d
    echo "⏳ Waiting for containers to be ready..."
    sleep 5
fi

# Check if containers are running
POSTGRES_RUNNING=$(docker ps --format '{{.Names}}' | grep -c "enrichment_postgres" || true)
APP_RUNNING=$(docker ps --format '{{.Names}}' | grep -c "enrichment_app" || true)

if [ "$POSTGRES_RUNNING" -eq 0 ]; then
    echo "❌ PostgreSQL container is not running."
    echo "   Starting containers..."
    docker compose up -d
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 10
fi

if [ "$APP_RUNNING" -eq 0 ]; then
    echo "❌ App container is not running."
    echo "   Starting containers..."
    docker compose up -d
    sleep 5
fi

# Check network connectivity
echo "🔗 Checking network connectivity..."
docker compose exec -T postgres pg_isready -U enrichment_user > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready!"
else
    echo "⚠️  PostgreSQL might still be starting. Wait a few seconds and try again."
fi

echo ""
echo "📊 Container status:"
docker compose ps
