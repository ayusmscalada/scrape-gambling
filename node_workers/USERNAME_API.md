# Username Storage API

This API endpoint allows Puppeteer workers to submit scraped usernames with platform information. The data is stored in memory and automatically saved to a CSV file.

## Endpoints

### POST `/usernames`

Submit usernames to be stored.

**Single username:**
```bash
curl -X POST http://localhost:3000/usernames \
  -H "Content-Type: application/json" \
  -d '{
    "username": "player123",
    "platform": "stake"
  }'
```

**Multiple usernames:**
```bash
curl -X POST http://localhost:3000/usernames \
  -H "Content-Type: application/json" \
  -d '{
    "usernames": [
      {"username": "player1", "platform": "stake"},
      {"username": "player2", "platform": "roobet"},
      {"username": "player3", "platform": "bcgame"}
    ]
  }'
```

**Response:**
```json
{
  "success": true,
  "added": 2,
  "skipped": 1,
  "message": "Added 2 usernames, skipped 1 duplicates"
}
```

### GET `/usernames`

Retrieve stored usernames.

**Get all usernames:**
```bash
curl http://localhost:3000/usernames
```

**Filter by platform:**
```bash
curl "http://localhost:3000/usernames?platform=stake"
```

**Limit results:**
```bash
curl "http://localhost:3000/usernames?limit=10"
```

**Response:**
```json
{
  "success": true,
  "count": 2,
  "usernames": [
    {
      "username": "player1",
      "platform": "stake",
      "timestamp": "2026-03-13T10:30:00.000Z"
    },
    {
      "username": "player2",
      "platform": "roobet",
      "timestamp": "2026-03-13T10:29:00.000Z"
    }
  ]
}
```

### GET `/usernames/stats`

Get statistics about stored usernames.

```bash
curl http://localhost:3000/usernames/stats
```

**Response:**
```json
{
  "success": true,
  "stats": {
    "total": 150,
    "platforms": {
      "stake": 50,
      "roobet": 40,
      "bcgame": 30,
      "thrill": 20,
      "shuffle": 10
    },
    "oldest": "2026-03-13T08:00:00.000Z",
    "newest": "2026-03-13T10:30:00.000Z"
  }
}
```

### POST `/usernames/save`

Manually trigger CSV save (auto-save runs every 30 seconds).

```bash
curl -X POST http://localhost:3000/usernames/save
```

**Response:**
```json
{
  "success": true,
  "saved": 5,
  "message": "Saved 5 entries to CSV"
}
```

## CSV Format

The CSV file is saved at `scraped_usernames.csv` in the project root with the following format:

```csv
timestamp,username,platform
2026-03-13T10:30:00.000Z,player1,stake
2026-03-13T10:29:00.000Z,player2,roobet
2026-03-13T10:28:00.000Z,player3,bcgame
```

## Features

- **Duplicate Prevention**: Automatically skips duplicate usernames from the same platform within 5 minutes
- **Auto-save**: Automatically saves to CSV every 30 seconds
- **Graceful Shutdown**: Saves all data to CSV when the server shuts down
- **Memory Storage**: Keeps all usernames in memory for fast retrieval
- **Platform Filtering**: Filter usernames by platform
- **Statistics**: Get counts and statistics about stored usernames

## Usage in Puppeteer Workers

In your worker files (e.g., `workers/stake.js`), you can send scraped usernames to the API:

```javascript
// After scraping usernames
const usernames = ['player1', 'player2', 'player3'];

// Send to API
const response = await fetch('http://localhost:3000/usernames', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        usernames: usernames.map(username => ({
            username: username,
            platform: 'stake'
        }))
    })
});

const result = await response.json();
console.log(`Added ${result.added} usernames`);
```

## Notes

- The CSV file is created automatically on first use
- Duplicate entries (same username + platform within 5 minutes) are automatically skipped
- All timestamps are in ISO 8601 format
- The CSV file is saved in the project root directory
