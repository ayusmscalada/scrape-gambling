#!/bin/bash
# Setup script for Docker + PostgreSQL environment

set -e

echo "🚀 Setting up Social Enrichment CLI..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start containers
echo "📦 Building and starting containers..."
docker compose up -d --build

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "🗄️  Running database migrations..."
docker compose exec -T app alembic upgrade head || {
    echo "⚠️  Migration failed. This might be the first run."
    echo "   Creating initial migration..."
    docker compose exec -T app alembic revision --autogenerate -m "Initial migration" || true
    docker compose exec -T app alembic upgrade head || true
}

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   docker compose exec app python scan_socials.py antonyambriz --source-site Stake"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f app"
