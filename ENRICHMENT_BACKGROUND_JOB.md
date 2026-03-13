# Enrichment Background Job

## Overview

The enrichment background job automatically processes unchecked `raw_players` from PostgreSQL and enriches them with social media data. The job runs continuously in the background when `run_server.py` is started and stops when the server shuts down.

## Features

- ✅ **Automatic Processing**: Processes unchecked `raw_players` in batches
- ✅ **Configurable Intervals**: Runs at configurable intervals (default: 60 seconds)
- ✅ **Batch Processing**: Processes multiple players per run (default: 10)
- ✅ **Real-time Updates**: Emits WebSocket events when enrichment completes
- ✅ **Graceful Shutdown**: Stops cleanly when server shuts down
- ✅ **Error Handling**: Continues processing even if individual enrichments fail

## How It Works

1. **Startup**: When `run_server.py` starts, it initializes and starts the enrichment job service
2. **Periodic Execution**: The job runs at configured intervals (default: 60 seconds)
3. **Batch Selection**: Each run selects up to `batch_size` unchecked `raw_players` (players with no `identity_matches` or `qualified_leads`)
4. **Enrichment**: For each player, the job:
   - Normalizes the username and generates variants
   - Searches public social platforms (Telegram, Instagram, X, YouTube, Twitch, Kick)
   - Extracts evidence from candidate profiles
   - Scores and classifies matches
   - Saves results to `identity_matches` and `qualified_leads` tables
5. **WebSocket Events**: Emits real-time events to connected frontend clients:
   - `identity_match_added`: When a new identity match is created
   - `qualified_lead_updated`: When a qualified lead is created/updated
   - `stats_updated`: When statistics change
6. **Shutdown**: When the server stops, the job service stops gracefully

## Configuration

Environment variables (set in `.env` or `docker-compose.yml`):

```bash
# Enrichment job configuration
ENRICHMENT_INTERVAL_SECONDS=60      # How often to run the job (seconds)
ENRICHMENT_BATCH_SIZE=10             # How many players to process per run
ENRICHMENT_MAX_RESULTS=20            # Max candidates to discover per username

# API server configuration
API_PORT=5000                        # Flask API server port
```

## Database Schema

The enrichment job uses the following tables:

### `raw_players`
- Stores captured usernames from gambling platforms
- A player is considered "unchecked" if it has no `identity_matches` or `qualified_leads`

### `identity_matches`
- Stores discovered social media profile matches
- One `raw_player` can have multiple `identity_matches`
- Contains: platform, social_handle, social_url, match_score, confidence_label, evidence

### `qualified_leads`
- Stores the final lead classification for each `raw_player`
- One `raw_player` can have at most one `qualified_lead`
- Contains: best_contact_type, best_contact_value, confidence, confidence_label

## Enrichment Workflow

For each unchecked `raw_player`, the enrichment process follows these stages:

### Stage A: Normalization
- Generates username variants (lowercase, trimmed, without separators, etc.)
- Builds search queries for each variant

### Stage B: Public Discovery
- Searches public social platforms:
  - X (Twitter)
  - Telegram
  - Instagram
  - YouTube
  - Twitch
  - Kick
- Uses search queries like: `"<username>"`, `"<username> gambling"`, `"<username> Stake"`, etc.

### Stage C: Candidate Extraction
- Extracts evidence from candidate profiles:
  - Display name, bio, avatar
  - Public contact details (email, Telegram, website, Discord)
  - Platform mentions (Stake, Roobet, Rollbit, etc.)
  - Referral codes, wallet mentions
  - Language/region clues

### Stage D: Confidence Scoring
- Scores each candidate based on:
  - Exact username match: +30
  - Strong variant match: +20
  - Same avatar pattern: +25
  - Platform mention: +20
  - Referral code/wallet: +40
  - Language clues: +10
  - Inconsistencies: -15
  - No evidence: -20

### Stage E: Classification
- Classifies each candidate:
  - `exact match`
  - `likely match`
  - `weak match`
  - `no reliable match`
- Classifies the overall lead:
  - `no lead`: No reliable identity match found
  - `weak lead`: Likely identity match but no strong contact path
  - `usable lead`: Strong identity match with public contact path

### Stage F: Persistence
- Saves `identity_matches` for all candidates
- Creates/updates `qualified_lead` if classification is `weak lead` or `usable lead`
- Emits WebSocket events for real-time frontend updates

## WebSocket Events

The enrichment job emits the following WebSocket events:

### `identity_match_added`
Emitted when a new identity match is created:
```json
{
  "id": 123,
  "raw_player_id": 456,
  "username": "player123",
  "source_site": "stake",
  "platform": "telegram",
  "social_handle": "player123",
  "social_url": "https://t.me/player123",
  "match_score": 72,
  "confidence_label": "likely match",
  "created_at": "2026-03-13T10:30:00Z"
}
```

### `qualified_lead_updated`
Emitted when a qualified lead is created or updated:
```json
{
  "id": 789,
  "raw_player_id": 456,
  "username": "player123",
  "source_site": "stake",
  "best_contact_type": "telegram",
  "best_contact_value": "@player123",
  "confidence": 72,
  "confidence_label": "usable lead",
  "created_at": "2026-03-13T10:30:00Z"
}
```

### `stats_updated`
Emitted when statistics change:
```json
{
  "total_raw_players": 1000,
  "total_qualified_leads": 150,
  "total_identity_matches": 500,
  "by_platform": {
    "stake": 400,
    "roobet": 300,
    "thrill": 200,
    "shuffle": 100
  }
}
```

## Monitoring

### Logs
The enrichment job logs important events:
- Batch start/completion
- Individual player enrichment progress
- Errors and warnings
- Statistics

### Statistics
You can check enrichment statistics via the job service:
```python
from app.jobs.enrichment_job import EnrichmentJobService

job = EnrichmentJobService()
stats = job.get_stats()
print(stats)
```

Returns:
```python
{
    'is_running': True,
    'interval_seconds': 60,
    'batch_size': 10,
    'total_raw_players': 1000,
    'enriched_count': 850,
    'unchecked_count': 150,
}
```

## Manual Triggering

For testing, you can manually trigger an enrichment batch:
```python
from app.jobs.enrichment_job import EnrichmentJobService

job = EnrichmentJobService()
job.start()
job.trigger_now()  # Manually trigger a batch
```

## Troubleshooting

### Job Not Running
- Check that `run_server.py` started successfully
- Verify PostgreSQL is accessible
- Check logs for errors

### No Players Being Processed
- Verify there are unchecked `raw_players` in the database
- Check that players don't already have `identity_matches` or `qualified_leads`
- Verify database connection

### Enrichment Failures
- Check logs for specific error messages
- Verify social platform search functions are working
- Check network connectivity
- Review rate limiting (delays between requests)

### WebSocket Events Not Received
- Verify frontend is connected to WebSocket
- Check that `socketio` instance is properly passed to enrichment job
- Review server logs for WebSocket errors

## Integration with Frontend

The React frontend automatically receives WebSocket events and updates:
- **Raw Players Table**: Shows all captured players
- **Identity Matches Table**: Updates when new matches are found
- **Qualified Leads Table**: Updates when leads are created/updated
- **Stats Panel**: Updates with latest statistics
- **Notification Center**: Shows real-time notifications for new matches and leads

## Performance Considerations

- **Batch Size**: Larger batches process more players but take longer
- **Interval**: Shorter intervals process players faster but use more resources
- **Rate Limiting**: Built-in delays prevent overwhelming social platforms
- **Database**: Uses connection pooling for efficient database access
- **Concurrency**: Single-threaded execution prevents database conflicts

## Future Enhancements

Potential improvements:
- Parallel processing of multiple players (with proper locking)
- Priority queue for important players
- Retry logic for failed enrichments
- Caching of search results
- Metrics and monitoring dashboard
- Export functionality for qualified leads
