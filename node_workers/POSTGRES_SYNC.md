# PostgreSQL Sync for Scraped Usernames

This module automatically syncs scraped usernames from the in-memory storage to PostgreSQL's `raw_players` table, which serves as the first step in the lead generation pipeline.

## Overview

The PostgreSQL sync runs automatically on an interval (default: 30 seconds) and:
1. Retrieves all usernames from the in-memory `usernameStorage`
2. Filters out already-synced entries (tracks last sync timestamp)
3. Inserts new usernames into PostgreSQL `raw_players` table
4. Handles duplicates gracefully (uses `ON CONFLICT DO NOTHING`)

## Configuration

### Environment Variables

The sync uses the following environment variables (with defaults):

```bash
POSTGRES_HOST=postgres          # PostgreSQL host (use 'postgres' in Docker, 'localhost' locally)
POSTGRES_PORT=5432              # PostgreSQL port
POSTGRES_DB=enrichment_db      # Database name
POSTGRES_USER=enrichment_user  # Database user
POSTGRES_PASSWORD=enrichment_pass  # Database password
POSTGRES_SYNC_INTERVAL_MS=30000   # Sync interval in milliseconds (default: 30 seconds)
```

### Docker Compose

The `puppeteer-service` container is configured with PostgreSQL environment variables in `docker-compose.yml`:

```yaml
puppeteer-service:
  environment:
    POSTGRES_HOST: postgres
    POSTGRES_PORT: 5432
    POSTGRES_DB: ${POSTGRES_DB:-enrichment_db}
    POSTGRES_USER: ${POSTGRES_USER:-enrichment_user}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-enrichment_pass}
    POSTGRES_SYNC_INTERVAL_MS: ${POSTGRES_SYNC_INTERVAL_MS:-30000}
```

## Database Schema

Usernames are inserted into the `raw_players` table with the following structure:

```sql
CREATE TABLE raw_players (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    source_site VARCHAR(100),  -- Maps to 'platform' from scraped data
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_username_source ON raw_players(username, source_site);
```

## How It Works

1. **Automatic Sync**: Starts automatically when the server starts
2. **Incremental Sync**: Only syncs new entries since the last sync (tracks timestamp)
3. **Duplicate Handling**: Uses PostgreSQL's `ON CONFLICT DO NOTHING` to skip duplicates
4. **Transaction Safety**: Uses database transactions for batch inserts
5. **Error Handling**: Logs errors but continues running even if individual inserts fail

## API Endpoints

### POST `/sync/postgres`

Manually trigger a PostgreSQL sync.

**Example:**
```bash
curl -X POST http://localhost:3000/sync/postgres
```

**Response:**
```json
{
  "success": true,
  "synced": 15,
  "skipped": 3,
  "errors": 0,
  "message": "Synced 15 usernames to PostgreSQL (3 skipped, 0 errors)"
}
```

## Logging

The sync module logs the following events:

- **Connection**: `[PostgresSync] PostgreSQL connection successful`
- **Sync Start**: `[PostgresSync] Syncing X usernames to PostgreSQL...`
- **Sync Complete**: `[PostgresSync] Sync complete: X inserted, Y skipped (duplicates), Z errors`
- **Errors**: Individual insert errors are logged but don't stop the sync

## Graceful Shutdown

On server shutdown (SIGTERM/SIGINT):
1. Stops the auto-sync interval
2. Performs a final manual sync
3. Closes the database connection pool
4. Continues with other cleanup tasks

## Testing

### Test Connection

The sync module tests the PostgreSQL connection on initialization. Check server logs for:
```
[PostgresSync] PostgreSQL connection successful
```

### Manual Sync Test

```bash
# Trigger manual sync
curl -X POST http://localhost:3000/sync/postgres

# Check usernames in storage
curl http://localhost:3000/usernames/stats

# Verify in PostgreSQL
docker compose exec postgres psql -U enrichment_user -d enrichment_db -c "SELECT COUNT(*) FROM raw_players;"
```

## Troubleshooting

### Connection Failed

**Error:** `[PostgresSync] PostgreSQL connection failed`

**Solutions:**
1. Verify PostgreSQL container is running: `docker compose ps postgres`
2. Check environment variables are set correctly
3. Verify network connectivity (containers on same network)
4. Check PostgreSQL logs: `docker compose logs postgres`

### No Usernames Syncing

**Possible causes:**
1. No usernames in storage (check `/usernames/stats`)
2. All usernames already synced (check `lastSyncedTimestamp`)
3. Sync interval too long (reduce `POSTGRES_SYNC_INTERVAL_MS`)

### Duplicate Entries

The sync uses `ON CONFLICT DO NOTHING` based on the `(username, source_site)` combination. If you see "skipped" entries, they are likely duplicates.

## Integration with Lead Pipeline

The `raw_players` table is the first step in the lead generation pipeline:

1. **raw_players** ← Scraped usernames (this sync)
2. **identity_matches** ← Social enrichment results
3. **qualified_leads** ← Final qualified leads

Each scraped username becomes a `raw_player` record, which can then be enriched with social media data and classified as a lead.
