# Social Enrichment Background Job Service

This background job service automatically enriches unchecked `raw_players` from PostgreSQL with social media data.

## Overview

The enrichment job service:
1. Periodically queries PostgreSQL for unchecked `raw_players` (those without `identity_matches` or `qualified_leads`)
2. Runs social enrichment on each unchecked player
3. Saves enrichment results to `identity_matches` and `qualified_leads` tables
4. Processes players in batches to avoid overwhelming the system

## Quick Start

### Run the Job Service

```bash
# Basic usage (default: 60s interval, batch size 10)
python run_enrichment_job.py

# Custom interval and batch size
python run_enrichment_job.py --interval 120 --batch-size 5

# With database wait (useful in Docker)
python run_enrichment_job.py --wait-db
```

### In Docker

```bash
# Run in background
docker compose exec app python run_enrichment_job.py --wait-db &

# Or run as a separate service (add to docker-compose.yml)
```

## Configuration

### Command Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--interval` | `60` | Interval between batches (seconds) |
| `--batch-size` | `10` | Number of players to process per batch |
| `--max-results` | `20` | Max candidates to discover per username |
| `--wait-db` | `False` | Wait for PostgreSQL to be ready |
| `--verbose` | `False` | Enable verbose logging |

### Environment Variables

The service uses the same PostgreSQL configuration as the main app:
- `POSTGRES_HOST` (default: `postgres` in Docker, `localhost` locally)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_DB` (default: `enrichment_db`)
- `POSTGRES_USER` (default: `enrichment_user`)
- `POSTGRES_PASSWORD` (default: `enrichment_pass`)

## How It Works

### 1. Finding Unchecked Players

A `raw_player` is considered "unchecked" if:
- It has **no** `identity_matches` records, AND
- It has **no** `qualified_leads` record

The service queries for these players ordered by `captured_at` (oldest first).

### 2. Enrichment Process

For each unchecked player:
1. Calls `enrich_username()` from `scan_socials.py`
2. Normalizes username and generates variants
3. Discovers public social media candidates
4. Extracts evidence and scores matches
5. Classifies the lead

### 3. Saving Results

Results are saved to:
- **`identity_matches`**: One record per discovered social media profile
- **`qualified_leads`**: One record per `raw_player` (only if classification is "weak lead" or "usable lead")

### 4. Duplicate Prevention

The service checks if a player is already enriched before processing (race condition protection).

## Example Output

```
2026-03-13 10:30:00 [INFO] Starting enrichment batch (batch_size: 10)
2026-03-13 10:30:01 [INFO] Found 10 unchecked raw_players to enrich
2026-03-13 10:30:02 [INFO] Enriching raw_player 1: player123 (source: stake)
2026-03-13 10:30:15 [INFO] Created 3 identity matches for player123
2026-03-13 10:30:15 [INFO] Enrichment complete for player123: usable lead
2026-03-13 10:30:17 [INFO] Enriching raw_player 2: player456 (source: roobet)
...
2026-03-13 10:30:45 [INFO] Batch complete: 10 succeeded, 0 failed
```

## Monitoring

### Check Statistics

The service logs statistics periodically:
```
Stats: 150 enriched, 25 unchecked
```

### Database Queries

Check enrichment status directly in PostgreSQL:

```sql
-- Total raw_players
SELECT COUNT(*) FROM raw_players;

-- Enriched players (have matches or leads)
SELECT COUNT(*) FROM raw_players rp
WHERE EXISTS (
    SELECT 1 FROM identity_matches im WHERE im.raw_player_id = rp.id
) OR EXISTS (
    SELECT 1 FROM qualified_leads ql WHERE ql.raw_player_id = rp.id
);

-- Unchecked players
SELECT COUNT(*) FROM raw_players rp
WHERE NOT EXISTS (
    SELECT 1 FROM identity_matches im WHERE im.raw_player_id = rp.id
) AND NOT EXISTS (
    SELECT 1 FROM qualified_leads ql WHERE ql.raw_player_id = rp.id
);
```

## Integration with Pipeline

The complete pipeline flow:

1. **Scraping** → Workers scrape usernames → Stored in `usernameStorage` (Node.js)
2. **PostgreSQL Sync** → Usernames synced to `raw_players` table (every 30s)
3. **Enrichment** → Background job enriches unchecked `raw_players` (every 60s)
4. **Results** → Saved to `identity_matches` and `qualified_leads` tables

## Running as a Service

### Using systemd (Linux)

Create `/etc/systemd/system/enrichment-job.service`:

```ini
[Unit]
Description=Social Enrichment Background Job Service
After=network.target postgresql.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/scrape-gambling
Environment="POSTGRES_HOST=localhost"
Environment="POSTGRES_PORT=5433"
ExecStart=/usr/bin/python3 /path/to/scrape-gambling/run_enrichment_job.py --wait-db
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable enrichment-job
sudo systemctl start enrichment-job
sudo systemctl status enrichment-job
```

### Using Docker Compose

Add to `docker-compose.yml`:

```yaml
  enrichment-job:
    build: .
    container_name: enrichment_job
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-enrichment_db}
      POSTGRES_USER: ${POSTGRES_USER:-enrichment_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-enrichment_pass}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
    volumes:
      - .:/app
    networks:
      - enrichment_network
    command: python run_enrichment_job.py --wait-db --interval 60 --batch-size 10
    restart: unless-stopped
```

## Troubleshooting

### No Players Being Enriched

**Check:**
1. Are there unchecked players? (see database queries above)
2. Is the job service running? (check logs)
3. Are there errors in the logs?

### Enrichment Errors

**Common issues:**
- Network timeouts → Increase delays between enrichments
- Rate limiting → Reduce batch size or increase interval
- Database connection errors → Check PostgreSQL is running

### Performance Tuning

**For faster processing:**
- Increase `--batch-size` (but watch for rate limiting)
- Decrease `--interval` (but ensure previous batch completes)

**For slower, safer processing:**
- Decrease `--batch-size`
- Increase `--interval`
- Add delays in enrichment code

## API Integration (Future)

The job service could be extended with an HTTP API for:
- Starting/stopping the service
- Triggering manual batches
- Getting statistics
- Adjusting configuration

For now, use the CLI script directly.
