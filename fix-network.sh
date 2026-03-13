#!/bin/bash
# Fix Docker networking issues

set -e

echo "🔧 Fixing Docker networking..."

# Stop and remove existing containers
echo "🛑 Stopping existing containers..."
docker compose down 2>/dev/null || true

# Remove old network if it exists
echo "🧹 Cleaning up old networks..."
docker network rm scrape-gambling_enrichment_network 2>/dev/null || true

# Start containers fresh
echo "🚀 Starting containers..."
docker compose up -d

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready (15 seconds)..."
sleep 15

# Verify connectivity
echo "🔍 Verifying connectivity..."
if docker compose exec -T postgres pg_isready -U enrichment_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready!"
else
    echo "⚠️  PostgreSQL might need more time. Checking logs..."
    docker compose logs postgres | tail -10
    exit 1
fi

# Test app can reach postgres
echo "🔗 Testing app -> postgres connection..."
if docker compose exec -T app python -c "
from app.config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
print('✅ Connection successful!')
" 2>/dev/null; then
    echo "✅ App can connect to PostgreSQL!"
else
    echo "❌ App cannot connect to PostgreSQL. Check logs:"
    docker compose logs app | tail -10
    exit 1
fi

echo ""
echo "✅ All fixed! You can now run:"
echo "   docker compose exec app alembic upgrade head"
