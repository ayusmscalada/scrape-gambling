#!/bin/bash
# Fix migration and verify tables exist

set -e

echo "🔍 Checking database state..."

# Check if alembic_version table exists and what version is recorded
echo "Checking Alembic version..."
sudo docker compose exec -T postgres psql -U enrichment_user -d enrichment_db -c "SELECT * FROM alembic_version;" 2>/dev/null || echo "No alembic_version table found"

echo ""
echo "Checking for tables..."
sudo docker compose exec -T postgres psql -U enrichment_user -d enrichment_db -c "\dt" || echo "No tables found"

echo ""
echo "🔧 Fixing migration..."

# Downgrade to base (removes all tables if migration was applied)
echo "Downgrading to base..."
sudo docker compose exec -T app alembic downgrade base 2>&1 || echo "Downgrade completed or not needed"

# Upgrade to head (creates all tables)
echo ""
echo "Running migration upgrade..."
sudo docker compose exec -T app alembic upgrade head

echo ""
echo "✅ Verifying tables were created..."
sudo docker compose exec -T postgres psql -U enrichment_user -d enrichment_db -c "\dt"

echo ""
echo "📊 Table details:"
sudo docker compose exec -T postgres psql -U enrichment_user -d enrichment_db -c "
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
"
